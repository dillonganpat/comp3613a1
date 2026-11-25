# CampusStay

A student accommodation marketplace for UWI St. Augustine. Landlords list rooms near campus, and students search, view and book them.

**Live app:** https://faststarter.onrender.com (free tier, so the first load may take about a minute)

Built for COMP 3613 (Software Engineering II), Assignments 1 and 2.
Stack: FastAPI, SQLModel, PostgreSQL (SQLite for local development), JWT, pytest, Postman, deployed on Render.

## Features

Three role-based workflows:

1. **Search and browse listings (tenant):** filter by location and nightly price, then view listing details.
2. **List a property (landlord):** create and delete your own listings.
3. **Book a listing (tenant):** pick check-in and check-out dates and get a total price.

Business rules enforced on the server:

- Every account has exactly one role: tenant or landlord.
- Only a landlord can list a property, and only its owner can delete it.
- A property that has bookings cannot be deleted.
- Check-in cannot be in the past, and check-out must be after check-in.
- Overlapping bookings for the same property are rejected (409). Back-to-back stays are allowed.
- Total price is nights multiplied by the nightly rate, and a new booking starts as `pending`.

## REST API

Sign in with `POST /api/auth`, then send `Authorization: Bearer <token>`.

| Method | Route | Access |
|---|---|---|
| POST | `/api/signup` | Public, creates a tenant |
| POST | `/api/auth` | Public, returns a JWT |
| GET | `/api/properties` | Signed in, filter by location and price |
| GET | `/api/properties/{id}` | Signed in |
| POST | `/api/properties` | Landlord |
| DELETE | `/api/properties/{id}` | Owning landlord |
| POST | `/api/bookings` | Tenant |
| GET | `/api/bookings/mine` | Tenant, own bookings only |
| GET | `/api/users` | Landlord, never returns password data |

Passwords are stored as Argon2 hashes.

## Testing

132 automated tests plus a Postman collection:

- 46 unit tests (mocked repositories, no database)
- 86 integration tests (real in-memory database and HTTP requests)
- 40 Postman requests with 75 assertions (`postman/CampusStay_API.postman_collection.json`)
- 15 manual user acceptance test cases

Testing found and fixed three defects: a 500 crash when booking a non-existent property, a server error when deleting a property that has bookings, and a user list that was visible without signing in.

## Run locally

```bash
git clone https://github.com/dillonganpat/comp3613a1.git
cd comp3613a1
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py init      # creates tables and demo users
python manage.py run       # http://127.0.0.1:5000
pytest -v                  # run all tests
```

Demo logins: `bob` / `bobpass` (tenant), `admin` / `adminpass` (landlord).

## Design documents

- Use case diagram: `docs/diagrams/use-case.png`
- Wireframes: `docs/wireframes/`
- Full report: `docs/report.pdf`

## Credits

Started from the FastStarter template provided by the course ([uwidcit/comp3613a1](https://github.com/uwidcit/comp3613a1)).
