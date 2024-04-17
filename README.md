# UniHaven

Multi-university off-campus accommodation platform with geospatial search, reservation management, and real-time notifications. Built with Django REST Framework for the CEDARS housing offices at HKU, HKUST, and CUHK.

`Django` `DRF` `OpenAPI` `SQLite` `Tailwind CSS`

<p align="center">
  <img src="docs/student_results.png" alt="Student search portal" width="100%">
</p>

## What it does

Students search for off-campus housing near their campus, filter by price/type/distance/dates, book accommodations, and rate them after checkout. Housing specialists manage listings, confirm or cancel reservations, and receive notifications, all scoped to their own university.

Two separate web portals hit the same REST API.

## Architecture

```
Student Portal ──┐                    ┌── DATA.GOV.HK
                 ├── DRF ViewSets ────┤   Address Lookup API
Specialist UI ───┘    (REST API)      └── Email (SMTP)
                         │
              ┌──────────┼──────────┐
              │          │          │
           Models    Serializers  Filters
              │
           SQLite
```

Three-layer design: Models define the schema, Serializers handle validation and nested representation, ViewSets expose filtered querysets with custom actions (confirm, cancel, complete, rate).

Each university sees only its own accommodations, reservations, and notifications. Achieved through a `universities` M2M field on Accommodation and a `university` FK on Reservation/Notification, with query parameter filtering in each ViewSet.

<p align="center">
  <img src="docs/domain_model.jpg" alt="Domain model" width="85%">
</p>

## Screenshots

| Student Portal | Specialist Dashboard |
|:-:|:-:|
| ![search](docs/student_results.png) | ![dashboard](docs/specialist_accommodations.png) |
| ![detail](docs/student_detail.png) | ![reservations](docs/specialist_reservations.png) |

<details>
<summary>More screenshots</summary>

| Notifications | Swagger API |
|:-:|:-:|
| ![notifications](docs/specialist_notifications.png) | ![swagger](docs/swagger_api.png) |

</details>

## API

7 resource endpoints, all following REST conventions. Full OpenAPI 3.0 schema in `API_schema.yaml`.

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/api/accommodations/` | GET, POST, PUT, DELETE | Listings with distance filtering, university scoping |
| `/api/reservations/` | GET, POST, PUT, DELETE | Booking with overlap prevention, status lifecycle |
| `/api/reservations/{id}/confirm/` | POST | Specialist confirms a pending booking |
| `/api/reservations/{id}/cancel/` | POST | Cancel with email notification |
| `/api/reservations/{id}/complete/` | POST | Mark as completed, triggers rating eligibility |
| `/api/ratings/` | GET, POST | Post-checkout ratings, one per user per accommodation |
| `/api/notifications/` | GET, POST | University-scoped, mark-as-read support |
| `/api/locations/lookup_address/` | POST | Geocode via DATA.GOV.HK Address Lookup Service |
| `/api/universities/` | GET, POST, PUT, DELETE | University CRUD |
| `/api/owners/` | GET, POST, PUT, DELETE | Property owner management |

Interactive docs at `/api/swagger/` and `/api/redoc/`.

## Notable implementation details

**Geospatial distance filtering.** Accommodations can be sorted and filtered by distance from a campus using equirectangular approximation. The calculation runs in Python on the queryset results, not in SQL, which is fine for the dataset size but would need PostGIS for production scale.

**Reservation overlap prevention.** When creating a booking, the system checks for any existing active reservation (pending or confirmed) whose date range overlaps with the requested period. Uses `start_date__lt=end_date, end_date__gt=start_date` exclusion logic.

**Address geocoding.** The `/api/locations/lookup_address/` endpoint hits the DATA.GOV.HK Address Lookup Service, parses the nested JSON response (building name, street, district, region), extracts lat/lng from GeospatialInformation, and creates a Location record.

**Rating guard.** Users can only rate an accommodation after completing a reservation for it (status=completed and end_date in the past). Duplicate ratings are rejected via unique_together constraint.

**Test suite.** 25+ test cases covering distance calculation, university CRUD, accommodation filtering (by university, by distance, sorting), reservation lifecycle (create, overlap rejection, outside-availability rejection, cancel, confirm, complete), rating eligibility, and notification filtering.

## SE Process Documentation

Full software engineering artifacts are in `docs/`:

| Document | Contents |
|----------|----------|
| [Vision Document](docs/VisionDocument_GroupG.pdf) | Business requirements, scope, stakeholders, release plan |
| [Use Cases](docs/UseCase_GroupG.pdf) | 8 fully-dressed use cases (UC1-UC8) with alternative flows |
| [Domain Model](docs/domain_model.jpg) | Entity relationships across University, Accommodation, Reservation, Rating, Notification |
| [Sprint 1 Backlog](docs/Sprint1%20Backlog_GroupG.pdf) | Models, CRUD endpoints, admin |
| [Sprint 2 Backlog](docs/Sprint2%20Backlog_GroupG.pdf) | Reservations, notifications, search, distance filtering |
| [Sprint 3 Backlog](docs/Sprint3%20backlog_GroupG.pdf) | Multi-university, rating system, UI, tests |
| [Mockups](docs/UniHaven_Mock-ups_GroupG.pdf) | Balsamiq wireframes for both portals |
| [Changes](docs/Addition%20and%20Modification_GroupG.pdf) | Release 2 modifications from Release 1 |

## Project structure

```
accommodation/
  models.py          University, Owner, Location, Accommodation, Reservation, Rating, Notification
  views.py           ViewSets with custom actions and distance filtering
  serializers.py     Nested serializers with write-only ID fields
  utils.py           Haversine distance, DATA.GOV.HK address lookup
  tests.py           25+ integration tests
  templates/
    test_search.html          Student search portal (Tailwind CSS)
    specialist_dashboard.html Specialist management dashboard (Tailwind CSS)
  management/commands/
    create_sample_data.py     Campus + accommodation seeder
api/
  urls.py            DRF router + Swagger/ReDoc
unihaven8/
  settings.py        Django config
  urls.py            Root URL routing
docs/                SE process artifacts, screenshots, domain model
API_schema.yaml      OpenAPI 3.0 specification
requirements.txt     Python dependencies
```

## Quick start

```bash
git clone https://github.com/Liyux3/unihaven.git
cd unihaven
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Student portal at `http://localhost:8000/student/`, specialist dashboard at `http://localhost:8000/specialist/`, API docs at `http://localhost:8000/api/swagger/`.

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend | Django, Django REST Framework |
| API docs | drf-yasg (Swagger, ReDoc), OpenAPI 3.0 |
| Database | SQLite (development), compatible with PostgreSQL |
| Frontend | Django templates, Tailwind CSS (CDN), vanilla JavaScript |
| External API | DATA.GOV.HK Address Lookup Service |
| Testing | Django TestCase, DRF APIClient |
