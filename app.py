import os
from functools import wraps
from secrets import compare_digest

from flask import Flask, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from prometheus_client import Counter, Gauge
from prometheus_flask_exporter import PrometheusMetrics
from sqlalchemy import func, text
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()
metrics = PrometheusMetrics.for_app_factory(group_by="endpoint")

LOGIN_FAILURES = Counter(
    "healthops_login_failures_total",
    "Number of failed interactive login attempts.",
)
PATIENT_MUTATIONS = Counter(
    "healthops_patient_mutations_total",
    "Number of patient create, update, and delete operations.",
    ["operation"],
)
PATIENT_COUNT = Gauge(
    "healthops_patients_total",
    "Current number of patients stored by the backend.",
)
USER_COUNT = Gauge(
    "healthops_users_total",
    "Current number of registered users stored by the backend.",
)
DATABASE_UP = Gauge(
    "healthops_database_up",
    "Database connectivity health reported during Prometheus scrapes.",
)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    disease = db.Column(db.String(200))


def normalize_database_uri(database_uri):
    if database_uri.startswith("postgres://"):
        return database_uri.replace("postgres://", "postgresql+psycopg://", 1)
    if database_uri.startswith("postgresql://"):
        return database_uri.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_uri


def database_is_ready():
    try:
        db.session.execute(text("SELECT 1"))
        return True
    except Exception:
        db.session.rollback()
        return False


def patient_to_dict(patient):
    return {
        "id": patient.id,
        "name": patient.name,
        "age": patient.age,
        "disease": patient.disease,
    }


def parse_patient_payload(payload):
    name = (payload.get("name") or "").strip()
    disease = (payload.get("disease") or "").strip()
    age_value = payload.get("age")

    if not name:
        return None, "Patient name is required."

    if not disease:
        return None, "Disease is required."

    try:
        age = int(age_value)
    except (TypeError, ValueError):
        return None, "Age must be a valid integer."

    if age <= 0:
        return None, "Age must be greater than zero."

    return {"name": name, "age": age, "disease": disease}, None


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "danger")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped_view


def api_auth_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if session.get("user_id"):
            return view_func(*args, **kwargs)

        configured_token = (current_app.config.get("API_TOKEN") or "").strip()
        auth_header = request.headers.get("Authorization", "")
        bearer_token = auth_header.replace("Bearer ", "", 1).strip() if auth_header.startswith("Bearer ") else ""
        api_key = request.headers.get("X-API-Key", "").strip()
        supplied_token = bearer_token or api_key

        if configured_token and supplied_token and compare_digest(supplied_token, configured_token):
            return view_func(*args, **kwargs)

        return jsonify({"error": "Authentication required."}), 401

    return wrapped_view


def create_app():
    flask_app = Flask(__name__)
    os.makedirs(flask_app.instance_path, exist_ok=True)

    default_sqlite_path = os.path.join(flask_app.instance_path, "patient.db")
    database_uri = normalize_database_uri(
        os.getenv("DATABASE_URL", f"sqlite:///{default_sqlite_path}")
    )

    flask_app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "healthops_super_secret_key"),
        API_TOKEN=os.getenv("API_TOKEN", "healthops-api-token"),
        SQLALCHEMY_DATABASE_URI=database_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
        JSON_SORT_KEYS=False,
    )

    db.init_app(flask_app)
    metrics.init_app(flask_app)
    metrics.info(
        "healthops_app_info",
        "HealthOps backend build information.",
        service="healthops-backend",
        runtime="flask",
    )

    with flask_app.app_context():
        PATIENT_COUNT.set_function(lambda: Patient.query.count())
        USER_COUNT.set_function(lambda: User.query.count())
        DATABASE_UP.set_function(lambda: 1 if database_is_ready() else 0)
        db.create_all()

    register_routes(flask_app)
    return flask_app


def register_routes(flask_app):
    @flask_app.route("/", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form["username"].strip()
            password = request.form["password"]
            user = User.query.filter_by(username=username).first()

            if user and check_password_hash(user.password_hash, password):
                session["user_id"] = user.id
                session["username"] = user.username
                flash("Logged in successfully.", "success")
                return redirect(url_for("dashboard"))

            LOGIN_FAILURES.inc()
            flash("Invalid username or password.", "danger")

        return render_template("login.html")

    @flask_app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form["username"].strip()
            password = request.form["password"]

            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash("Username already exists. Please choose another one.", "danger")
                return redirect(url_for("register"))

            new_user = User(
                username=username,
                password_hash=generate_password_hash(password),
            )
            db.session.add(new_user)
            db.session.commit()

            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))

        return render_template("register.html")

    @flask_app.route("/logout")
    def logout():
        session.pop("user_id", None)
        session.pop("username", None)
        flash("You have been logged out.", "info")
        return redirect(url_for("login"))

    @flask_app.route("/dashboard")
    @login_required
    def dashboard():
        return render_template("dashboard.html")

    @flask_app.route("/add", methods=["GET", "POST"])
    @login_required
    def add_patient():
        if request.method == "POST":
            patient_data, error_message = parse_patient_payload(request.form)
            if error_message:
                flash(error_message, "danger")
                return redirect(url_for("add_patient"))

            patient = Patient(**patient_data)
            db.session.add(patient)
            db.session.commit()
            PATIENT_MUTATIONS.labels(operation="create").inc()

            flash("Patient added successfully.", "success")
            return redirect(url_for("view_patients"))

        return render_template("add_patient.html")

    @flask_app.route("/patients")
    @login_required
    def view_patients():
        patients = Patient.query.order_by(Patient.id.desc()).all()
        return render_template("view_patients.html", patients=patients)

    @flask_app.route("/update/<int:id>", methods=["GET", "POST"])
    @login_required
    def update_patient(id):
        patient = db.session.get(Patient, id)
        if patient is None:
            flash("Patient not found.", "danger")
            return redirect(url_for("view_patients"))

        if request.method == "POST":
            patient_data, error_message = parse_patient_payload(request.form)
            if error_message:
                flash(error_message, "danger")
                return redirect(url_for("update_patient", id=id))

            patient.name = patient_data["name"]
            patient.age = patient_data["age"]
            patient.disease = patient_data["disease"]
            db.session.commit()
            PATIENT_MUTATIONS.labels(operation="update").inc()

            flash("Patient updated successfully.", "success")
            return redirect(url_for("view_patients"))

        return render_template("update_patient.html", patient=patient)

    @flask_app.route("/delete/<int:id>")
    @login_required
    def delete_patient(id):
        patient = db.session.get(Patient, id)
        if patient is None:
            flash("Patient not found.", "danger")
            return redirect(url_for("view_patients"))

        db.session.delete(patient)
        db.session.commit()
        PATIENT_MUTATIONS.labels(operation="delete").inc()
        flash("Patient deleted successfully.", "success")
        return redirect(url_for("view_patients"))

    @flask_app.get("/healthz")
    def healthz():
        return jsonify({"status": "ok"}), 200

    @flask_app.get("/readyz")
    def readyz():
        if database_is_ready():
            return jsonify({"status": "ready"}), 200
        return jsonify({"status": "degraded"}), 503

    @flask_app.get("/api/v1/summary")
    @api_auth_required
    def api_summary():
        average_age = db.session.query(func.avg(Patient.age)).scalar()
        disease_breakdown = (
            db.session.query(Patient.disease, func.count(Patient.id))
            .group_by(Patient.disease)
            .order_by(func.count(Patient.id).desc())
            .all()
        )

        return jsonify(
            {
                "patients_total": Patient.query.count(),
                "users_total": User.query.count(),
                "average_patient_age": round(float(average_age), 2) if average_age else None,
                "disease_breakdown": [
                    {"disease": disease, "count": total}
                    for disease, total in disease_breakdown
                ],
            }
        )

    @flask_app.route("/api/v1/patients", methods=["GET", "POST"])
    @api_auth_required
    def api_patients():
        if request.method == "GET":
            disease_filter = request.args.get("disease", "").strip()
            query = Patient.query
            if disease_filter:
                query = query.filter(Patient.disease.ilike(f"%{disease_filter}%"))

            patients = query.order_by(Patient.id.desc()).all()
            return jsonify({"items": [patient_to_dict(patient) for patient in patients]})

        payload = request.get_json(silent=True) or {}
        patient_data, error_message = parse_patient_payload(payload)
        if error_message:
            return jsonify({"error": error_message}), 400

        patient = Patient(**patient_data)
        db.session.add(patient)
        db.session.commit()
        PATIENT_MUTATIONS.labels(operation="create").inc()
        return jsonify(patient_to_dict(patient)), 201

    @flask_app.route("/api/v1/patients/<int:patient_id>", methods=["GET", "PUT", "DELETE"])
    @api_auth_required
    def api_patient_detail(patient_id):
        patient = db.session.get(Patient, patient_id)
        if patient is None:
            return jsonify({"error": "Patient not found."}), 404

        if request.method == "GET":
            return jsonify(patient_to_dict(patient))

        if request.method == "DELETE":
            db.session.delete(patient)
            db.session.commit()
            PATIENT_MUTATIONS.labels(operation="delete").inc()
            return "", 204

        payload = request.get_json(silent=True) or {}
        patient_data, error_message = parse_patient_payload(payload)
        if error_message:
            return jsonify({"error": error_message}), 400

        patient.name = patient_data["name"]
        patient.age = patient_data["age"]
        patient.disease = patient_data["disease"]
        db.session.commit()
        PATIENT_MUTATIONS.labels(operation="update").inc()
        return jsonify(patient_to_dict(patient))


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )
