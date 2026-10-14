from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

from db import get_db_connection
import os 


app = Flask(__name__)

app.secret_key = os.environ.get("FLASK_SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("FLASK_SECRET_KEY environment variable is not set")


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        prn = request.form["prn"]
        dept = request.form["dept"]
        password = request.form["password"]

        password_hash = generate_password_hash(password)

        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            # Insert into USER table
            cursor.execute(
                """
                INSERT INTO `USER`
                (name, email, password)
                VALUES (%s, %s, %s)
                """,
                (name, email, password_hash)
            )

            user_id = cursor.lastrowid

            # Insert into STUDENT table
            cursor.execute(
                """
                INSERT INTO STUDENT
                (user_id, PRN, dept)
                VALUES (%s, %s, %s)
                """,
                (user_id, prn, dept)
            )

            connection.commit()

        except Exception as e:

            connection.rollback()

            cursor.close()
            connection.close()

            return f"Registration failed: {e}"

        cursor.close()
        connection.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        # Connect to database
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Find user by email
        cursor.execute(
            """
            SELECT *
            FROM `USER`
            WHERE email = %s
            """,
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        # Check email and password
        if user and check_password_hash(
            user["password"],
            password
        ):

            # Store logged-in user's ID
            session["user_id"] = user["user_id"]

            # Check whether this user is an admin
            connection = get_db_connection()
            admin_cursor = connection.cursor(dictionary=True)

            admin_cursor.execute(
                """
                SELECT admin_id
                FROM ADMIN
                WHERE user_id = %s
                """,
                (user["user_id"],)
            )

            admin = admin_cursor.fetchone()

            admin_cursor.close()
            connection.close()

            # Admin → Admin Dashboard
            if admin:
                return redirect(url_for("admin_dashboard"))

            # Student → Student Dashboard
            return redirect(url_for("dashboard"))

        # Login failed: show a useful message on the login page.
        if not user:
            flash("Account not found. Please register first.", "error")
        else:
            flash("Incorrect password. Please try again.", "error")

        return redirect(url_for("login"))

    # Show login page
    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# =========================================================
# STUDENT DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Get user information
    cursor.execute(
        """
        SELECT name, email
        FROM `USER`
        WHERE user_id = %s
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    # Get student ID
    cursor.execute(
        """
        SELECT student_id
        FROM STUDENT
        WHERE user_id = %s
        """,
        (user_id,)
    )

    student = cursor.fetchone()

    lost_items = []
    found_items = []

    lost_count = 0
    found_count = 0

    if student:

        student_id = student["student_id"]

        # Get student's lost items
        cursor.execute(
            """
            SELECT
                LOST_ITEM.lost_item_id,
                CATEGORY.category_name,
                LOCATION.location_name,
                LOST_ITEM.description,
                LOST_ITEM.date_reported,
                LOST_ITEM.status
            FROM LOST_ITEM

            JOIN CATEGORY
                ON LOST_ITEM.category_id =
                   CATEGORY.category_id

            JOIN LOCATION
                ON LOST_ITEM.location_id =
                   LOCATION.location_id

            WHERE LOST_ITEM.student_id = %s

            ORDER BY LOST_ITEM.lost_item_id DESC
            """,
            (student_id,)
        )

        lost_items = cursor.fetchall()

        # Get student's found items
        cursor.execute(
            """
            SELECT
                FOUND_ITEM.found_item_id,
                CATEGORY.category_name,
                LOCATION.location_name,
                FOUND_ITEM.description,
                FOUND_ITEM.date_reported,
                FOUND_ITEM.status
            FROM FOUND_ITEM

            JOIN CATEGORY
                ON FOUND_ITEM.category_id =
                   CATEGORY.category_id

            JOIN LOCATION
                ON FOUND_ITEM.location_id =
                   LOCATION.location_id

            WHERE FOUND_ITEM.student_id = %s

            ORDER BY FOUND_ITEM.found_item_id DESC
            """,
            (student_id,)
        )

        found_items = cursor.fetchall()

        lost_count = len(lost_items)
        found_count = len(found_items)

    # Notification count
    cursor.execute(
        """
        SELECT COUNT(*) AS notification_count
        FROM NOTIFICATION
        WHERE user_id = %s
        AND is_read = FALSE
        """,
        (user_id,)
    )

    notification_data = cursor.fetchone()

    notification_count = notification_data["notification_count"]

    cursor.close()
    connection.close()

    return render_template(
        "dashboard.html",
        user=user,
        lost_items=lost_items,
        found_items=found_items,
        lost_count=lost_count,
        found_count=found_count,
        notification_count=notification_count
    )


# =========================================================
# REPORT LOST ITEM
# =========================================================

@app.route("/report-lost", methods=["GET", "POST"])
def report_lost():

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Load categories
    cursor.execute(
        """
        SELECT *
        FROM CATEGORY
        ORDER BY category_name
        """
    )

    categories = cursor.fetchall()

    # Load locations
    cursor.execute(
        """
        SELECT *
        FROM LOCATION
        ORDER BY location_name
        """
    )

    locations = cursor.fetchall()

    if request.method == "POST":

        category_id = request.form["category_id"]
        location_id = request.form["location_id"]
        description = request.form["description"]
        date_reported = request.form["date_reported"]

        # Find student
        cursor.execute(
            """
            SELECT student_id
            FROM STUDENT
            WHERE user_id = %s
            """,
            (user_id,)
        )

        student = cursor.fetchone()

        if not student:

            cursor.close()
            connection.close()

            return "Student account not found."

        student_id = student["student_id"]

        # Insert lost item
        cursor.execute(
            """
            INSERT INTO LOST_ITEM
            (
                student_id,
                category_id,
                location_id,
                description,
                date_reported,
                status
            )

            VALUES
            (%s, %s, %s, %s, %s, %s)
            """,
            (
                student_id,
                category_id,
                location_id,
                description,
                date_reported,
                "Open"
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("dashboard"))

    cursor.close()
    connection.close()

    return render_template(
        "report_lost.html",
        categories=categories,
        locations=locations
    )


# =========================================================
# REPORT FOUND ITEM
# =========================================================

@app.route("/report-found", methods=["GET", "POST"])
def report_found():

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Load categories
    cursor.execute(
        """
        SELECT *
        FROM CATEGORY
        ORDER BY category_name
        """
    )

    categories = cursor.fetchall()

    # Load locations
    cursor.execute(
        """
        SELECT *
        FROM LOCATION
        ORDER BY location_name
        """
    )

    locations = cursor.fetchall()

    if request.method == "POST":

        category_id = request.form["category_id"]
        location_id = request.form["location_id"]
        description = request.form["description"]
        date_reported = request.form["date_reported"]

        # Find student
        cursor.execute(
            """
            SELECT student_id
            FROM STUDENT
            WHERE user_id = %s
            """,
            (user_id,)
        )

        student = cursor.fetchone()

        if not student:

            cursor.close()
            connection.close()

            return "Student account not found."

        student_id = student["student_id"]

        # Insert found item
        cursor.execute(
            """
            INSERT INTO FOUND_ITEM
            (
                student_id,
                category_id,
                location_id,
                description,
                date_reported,
                status
            )

            VALUES
            (%s, %s, %s, %s, %s, %s)
            """,
            (
                student_id,
                category_id,
                location_id,
                description,
                date_reported,
                "Available"
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("dashboard"))

    cursor.close()
    connection.close()

    return render_template(
        "report_found.html",
        categories=categories,
        locations=locations
    )


# =========================================================
# BROWSE ITEMS
# =========================================================

@app.route("/items")
def browse_items():

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Lost items
    cursor.execute(
        """
        SELECT
            LOST_ITEM.lost_item_id,
            USER.name AS student_name,
            CATEGORY.category_name,
            LOCATION.location_name,
            LOST_ITEM.description,
            LOST_ITEM.date_reported,
            LOST_ITEM.status
        FROM LOST_ITEM

        JOIN STUDENT
            ON LOST_ITEM.student_id =
               STUDENT.student_id

        JOIN `USER`
            ON STUDENT.user_id =
               `USER`.user_id

        JOIN CATEGORY
            ON LOST_ITEM.category_id =
               CATEGORY.category_id

        JOIN LOCATION
            ON LOST_ITEM.location_id =
               LOCATION.location_id

        WHERE LOST_ITEM.status = 'Open'

        ORDER BY LOST_ITEM.lost_item_id DESC
        """
    )

    lost_items = cursor.fetchall()

    # Found items
    cursor.execute(
        """
        SELECT
            FOUND_ITEM.found_item_id,
            USER.name AS student_name,
            CATEGORY.category_name,
            LOCATION.location_name,
            FOUND_ITEM.description,
            FOUND_ITEM.date_reported,
            FOUND_ITEM.status
        FROM FOUND_ITEM

        JOIN STUDENT
            ON FOUND_ITEM.student_id =
               STUDENT.student_id

        JOIN `USER`
            ON STUDENT.user_id =
               `USER`.user_id

        JOIN CATEGORY
            ON FOUND_ITEM.category_id =
               CATEGORY.category_id

        JOIN LOCATION
            ON FOUND_ITEM.location_id =
               LOCATION.location_id

        WHERE FOUND_ITEM.status = 'Available'

        ORDER BY FOUND_ITEM.found_item_id DESC
        """
    )

    found_items = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "browse_items.html",
        lost_items=lost_items,
        found_items=found_items
    )


# =========================================================
# FIND MATCHES
# =========================================================

@app.route("/find-matches/<int:lost_item_id>")
def find_matches(lost_item_id):

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Get lost item
    cursor.execute(
        """
        SELECT
            lost_item_id,
            category_id,
            location_id
        FROM LOST_ITEM
        WHERE lost_item_id = %s
        """,
        (lost_item_id,)
    )

    lost_item = cursor.fetchone()

    if not lost_item:

        cursor.close()
        connection.close()

        return "Lost item not found."

    # Find possible matches
    cursor.execute(
        """
        SELECT
            FOUND_ITEM.found_item_id,
            CATEGORY.category_name,
            LOCATION.location_name,
            FOUND_ITEM.description,
            FOUND_ITEM.date_reported,
            FOUND_ITEM.status
        FROM FOUND_ITEM

        JOIN CATEGORY
            ON FOUND_ITEM.category_id =
               CATEGORY.category_id

        JOIN LOCATION
            ON FOUND_ITEM.location_id =
               LOCATION.location_id

        WHERE FOUND_ITEM.category_id = %s

        AND FOUND_ITEM.location_id = %s

        AND FOUND_ITEM.status = 'Available'
        """,
        (
            lost_item["category_id"],
            lost_item["location_id"]
        )
    )

    matches = cursor.fetchall()

    # Create MATCH records
    for item in matches:

        cursor.execute(
            """
            SELECT match_id
            FROM `MATCH`
            WHERE lost_item_id = %s
            AND found_item_id = %s
            """,
            (
                lost_item_id,
                item["found_item_id"]
            )
        )

        existing_match = cursor.fetchone()

        if not existing_match:

            cursor.execute(
                """
                INSERT INTO `MATCH`
                (
                    lost_item_id,
                    found_item_id,
                    match_score,
                    match_status,
                    created_at
                )

                VALUES
                (%s, %s, %s, %s, NOW())
                """,
                (
                    lost_item_id,
                    item["found_item_id"],
                    100,
                    "Pending"
                )
            )

    connection.commit()

    cursor.close()
    connection.close()

    return render_template(
        "browse_items.html",
        lost_items=[],
        found_items=matches,
        matches=True,
        lost_item_id=lost_item_id
    )


# =========================================================
# CLAIM FOUND ITEM
# =========================================================

@app.route("/claim/<int:found_item_id>", methods=["GET", "POST"])
def claim_item(found_item_id):

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Get student
    cursor.execute(
        """
        SELECT student_id
        FROM STUDENT
        WHERE user_id = %s
        """,
        (user_id,)
    )

    student = cursor.fetchone()

    if not student:

        cursor.close()
        connection.close()

        return "Student account not found."

    student_id = student["student_id"]

    if request.method == "POST":

        reason = request.form["reason"]

        # Check if already claimed
        cursor.execute(
            """
            SELECT claim_id
            FROM CLAIM
            WHERE student_id = %s
            AND found_item_id = %s
            AND status = 'Pending'
            """,
            (
                student_id,
                found_item_id
            )
        )

        existing_claim = cursor.fetchone()

        if existing_claim:

            cursor.close()
            connection.close()

            return "You have already submitted a claim for this item."

        # Insert claim
        cursor.execute(
            """
            INSERT INTO CLAIM
            (
                student_id,
                found_item_id,
                match_id,
                reason,
                status,
                admin_id,
                created_at,
                authorized_at
            )

            VALUES
            (%s, %s, NULL, %s, %s, NULL, NOW(), NULL)
            """,
            (
                student_id,
                found_item_id,
                reason,
                "Pending"
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("my_claims"))

    # Get found item
    cursor.execute(
        """
        SELECT
            FOUND_ITEM.found_item_id,
            CATEGORY.category_name,
            LOCATION.location_name,
            FOUND_ITEM.description,
            FOUND_ITEM.date_reported
        FROM FOUND_ITEM

        JOIN CATEGORY
            ON FOUND_ITEM.category_id =
               CATEGORY.category_id

        JOIN LOCATION
            ON FOUND_ITEM.location_id =
               LOCATION.location_id

        WHERE FOUND_ITEM.found_item_id = %s
        """,
        (found_item_id,)
    )

    found_item = cursor.fetchone()

    cursor.close()
    connection.close()

    return render_template(
        "my_claims.html",
        claim_form=True,
        found_item=found_item
    )


# =========================================================
# MY CLAIMS
# =========================================================

@app.route("/claims")
def my_claims():

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT student_id
        FROM STUDENT
        WHERE user_id = %s
        """,
        (user_id,)
    )

    student = cursor.fetchone()

    claims = []

    if student:

        cursor.execute(
            """
            SELECT
                CLAIM.claim_id,
                CLAIM.reason,
                CLAIM.status,
                CLAIM.created_at,
                FOUND_ITEM.found_item_id,
                FOUND_ITEM.description,
                CATEGORY.category_name,
                LOCATION.location_name
            FROM CLAIM

            JOIN FOUND_ITEM
                ON CLAIM.found_item_id =
                   FOUND_ITEM.found_item_id

            JOIN CATEGORY
                ON FOUND_ITEM.category_id =
                   CATEGORY.category_id

            JOIN LOCATION
                ON FOUND_ITEM.location_id =
                   LOCATION.location_id

            WHERE CLAIM.student_id = %s

            ORDER BY CLAIM.claim_id DESC
            """,
            (student["student_id"],)
        )

        claims = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "my_claims.html",
        claims=claims,
        claim_form=False
    )


# =========================================================
# NOTIFICATIONS
# =========================================================

@app.route("/notifications")
def notifications():

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            notification_id,
            message,
            type,
            is_read,
            created_at
        FROM NOTIFICATION

        WHERE user_id = %s

        ORDER BY notification_id DESC
        """,
        (user_id,)
    )

    notifications_list = cursor.fetchall()

    # Mark notifications as read
    cursor.execute(
        """
        UPDATE NOTIFICATION
        SET is_read = TRUE
        WHERE user_id = %s
        """,
        (user_id,)
    )

    connection.commit()

    cursor.close()
    connection.close()

    return render_template(
        "notifications.html",
        notifications=notifications_list
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
def admin_dashboard():

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Check whether user is admin
    cursor.execute(
        """
        SELECT admin_id
        FROM ADMIN
        WHERE user_id = %s
        """,
        (user_id,)
    )

    admin = cursor.fetchone()

    if not admin:

        cursor.close()
        connection.close()

        flash("Access denied. This page is for administrators only.", "error")
        return redirect(url_for("dashboard"))

    # Get all claims
    cursor.execute(
        """
        SELECT
            CLAIM.claim_id,

            CLAIM.reason,

            CLAIM.status,

            CLAIM.created_at,

            FOUND_ITEM.found_item_id,

            FOUND_ITEM.description
                AS found_description,

            CATEGORY.category_name,

            LOCATION.location_name,

            USER.name
                AS student_name,

            USER.email
                AS student_email

        FROM CLAIM

        JOIN STUDENT
            ON CLAIM.student_id =
               STUDENT.student_id

        JOIN `USER`
            ON STUDENT.user_id =
               `USER`.user_id

        JOIN FOUND_ITEM
            ON CLAIM.found_item_id =
               FOUND_ITEM.found_item_id

        JOIN CATEGORY
            ON FOUND_ITEM.category_id =
               CATEGORY.category_id

        JOIN LOCATION
            ON FOUND_ITEM.location_id =
               LOCATION.location_id

        ORDER BY CLAIM.claim_id DESC
        """
    )

    claims = cursor.fetchall()

    # Get match records for admin review.
    # Matching itself is rule-based in /find-matches/<lost_item_id>.
    cursor.execute(
        """
        SELECT
            `MATCH`.match_id,
            `MATCH`.lost_item_id,
            `MATCH`.found_item_id,
            `MATCH`.match_score,
            `MATCH`.match_status,
            `MATCH`.created_at,
            LOST_ITEM.description AS lost_description,
            FOUND_ITEM.description AS found_description,
            LOST_CATEGORY.category_name AS lost_category,
            FOUND_CATEGORY.category_name AS found_category,
            LOST_LOCATION.location_name AS lost_location,
            FOUND_LOCATION.location_name AS found_location
        FROM `MATCH`
        JOIN LOST_ITEM
            ON `MATCH`.lost_item_id = LOST_ITEM.lost_item_id
        JOIN FOUND_ITEM
            ON `MATCH`.found_item_id = FOUND_ITEM.found_item_id
        JOIN CATEGORY AS LOST_CATEGORY
            ON LOST_ITEM.category_id = LOST_CATEGORY.category_id
        JOIN CATEGORY AS FOUND_CATEGORY
            ON FOUND_ITEM.category_id = FOUND_CATEGORY.category_id
        JOIN LOCATION AS LOST_LOCATION
            ON LOST_ITEM.location_id = LOST_LOCATION.location_id
        JOIN LOCATION AS FOUND_LOCATION
            ON FOUND_ITEM.location_id = FOUND_LOCATION.location_id
        ORDER BY `MATCH`.match_id DESC
        """
    )

    matches = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "admin_dashboard.html",
        claims=claims,
        matches=matches
    )


# =========================================================
# ADMIN APPROVE CLAIM
# =========================================================

@app.route("/admin/approve/<int:claim_id>")
def approve_claim(claim_id):

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Check admin
    cursor.execute(
        """
        SELECT admin_id
        FROM ADMIN
        WHERE user_id = %s
        """,
        (user_id,)
    )

    admin = cursor.fetchone()

    if not admin:

        cursor.close()
        connection.close()

        return "Access denied."

    admin_id = admin["admin_id"]

    # Get claim
    cursor.execute(
        """
        SELECT
            claim_id,
            student_id,
            found_item_id
        FROM CLAIM
        WHERE claim_id = %s
        """,
        (claim_id,)
    )

    claim = cursor.fetchone()

    if not claim:

        cursor.close()
        connection.close()

        return "Claim not found."

    # Approve claim
    cursor.execute(
        """
        UPDATE CLAIM

        SET
            status = 'Approved',
            admin_id = %s,
            authorized_at = NOW()

        WHERE claim_id = %s
        """,
        (
            admin_id,
            claim_id
        )
    )

    # Mark found item as claimed
    cursor.execute(
        """
        UPDATE FOUND_ITEM

        SET status = 'Claimed'

        WHERE found_item_id = %s
        """,
        (claim["found_item_id"],)
    )

    # Get user's ID
    cursor.execute(
        """
        SELECT user_id
        FROM STUDENT
        WHERE student_id = %s
        """,
        (claim["student_id"],)
    )

    student = cursor.fetchone()

    if student:

        # Create notification
        cursor.execute(
            """
            INSERT INTO NOTIFICATION
            (
                user_id,
                message,
                type,
                is_read,
                created_at
            )

            VALUES
            (%s, %s, %s, FALSE, NOW())
            """,
            (
                student["user_id"],
                "Your claim has been approved by the administrator.",
                "Claim Approved"
            )
        )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect(url_for("admin_dashboard"))


# =========================================================
# ADMIN REJECT CLAIM
# =========================================================

@app.route("/admin/reject/<int:claim_id>")
def reject_claim(claim_id):

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Check admin
    cursor.execute(
        """
        SELECT admin_id
        FROM ADMIN
        WHERE user_id = %s
        """,
        (user_id,)
    )

    admin = cursor.fetchone()

    if not admin:

        cursor.close()
        connection.close()

        return "Access denied."

    admin_id = admin["admin_id"]

    # Get claim
    cursor.execute(
        """
        SELECT
            claim_id,
            student_id
        FROM CLAIM
        WHERE claim_id = %s
        """,
        (claim_id,)
    )

    claim = cursor.fetchone()

    if not claim:

        cursor.close()
        connection.close()

        return "Claim not found."

    # Reject claim
    cursor.execute(
        """
        UPDATE CLAIM

        SET
            status = 'Rejected',
            admin_id = %s,
            authorized_at = NOW()

        WHERE claim_id = %s
        """,
        (
            admin_id,
            claim_id
        )
    )

    # Get user's ID
    cursor.execute(
        """
        SELECT user_id
        FROM STUDENT
        WHERE student_id = %s
        """,
        (claim["student_id"],)
    )

    student = cursor.fetchone()

    if student:

        cursor.execute(
            """
            INSERT INTO NOTIFICATION
            (
                user_id,
                message,
                type,
                is_read,
                created_at
            )

            VALUES
            (%s, %s, %s, FALSE, NOW())
            """,
            (
                student["user_id"],
                "Your claim has been rejected by the administrator.",
                "Claim Rejected"
            )
        )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect(url_for("admin_dashboard"))


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    )