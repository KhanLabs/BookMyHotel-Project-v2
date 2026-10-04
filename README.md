# BookMyHotel

A hotel booking website built with Flask. You can browse and filter hotels, book a stay, use promo codes, leave reviews, and manage everything from an admin dashboard.

This is a demo project for learning. Payments are not real: the card form does not process or store card details, and the hotels are sample data.

## Features

- Hotel listing with search and filters (price range, work-friendly, has kitchen, eco-friendly)
- User registration/login with hashed passwords
- Booking flow with date validation, promo codes, and optional add-on services (car rental, spa, bar, city tour)
- Reward points for bookings at high-sustainability-rated hotels
- Reviews per hotel
- Admin dashboard: revenue/booking stats, add/edit/delete hotels, view users, promotions, and contact messages

## Requirements

- Python 3.9+

## Setup

```bash
pip install -r requirements.txt
python app.py
```

The database is created and seeded automatically on first run (`instance/bookmyhotel.db`). This file is not stored in the repo. Delete it to go back to the sample data.

## Admin login

Go to `/admin` and sign in with username `admin` and password `admin123`. These are demo details for running it on your own computer. If you put it online, change the admin password in `app.py` and set a `SECRET_KEY` environment variable.

## Known issues

- `templates/admin_cancel.html` and `templates/edit_user_admin.html` are left over from an earlier version of the admin panel. No page links to them.
- No automated tests.

## Project structure

| Path | Contents |
|---|---|
| `app.py` | Routes, models, and app setup |
| `templates/` | Jinja2 templates (Bootstrap-based) |
| `instance/` | SQLite database (created on first run, not stored in the repo) |

## License

MIT. See [LICENSE](LICENSE).
