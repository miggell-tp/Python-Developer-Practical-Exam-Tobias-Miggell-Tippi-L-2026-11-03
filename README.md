# Car Ledger

My submission for the Valens Research Python practical exam. It’s a Django app for managing an ordered list of cars in SQLite. The included database has 100,000 sample cars, so you can try the app as soon as it starts.

## Run it locally

From the repository folder in PowerShell, with Python 3.14 installed:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

To try a move, click **Move** next to a car and enter the ID of the car it should go in front of. Use the first car’s ID to move to the front, or leave the field blank to move to the end. A color filter changes which cars you see. The move still applies to the full list.

To populate a fresh database, run `.\.venv\Scripts\python.exe manage.py seed_cars`. The command adds enough sample cars to reach 100,000 and leaves existing cars in place. Use `--total 60` if you want a smaller dataset in a fresh database.

## Why I used spaced order keys

I gave each car an integer `order_key` and left a gap of 1,000,000 between newly appended cars. Suppose two cars have keys `100` and `200`. To move another car between them, I can give it key `150`. The move updates one row. Moving a car before itself or its immediate successor updates zero rows.

Repeated moves into the same gap can eventually use up the available integers. When that happens, the app spaces out the whole list again, then finishes the move in the same transaction. That makes a rebalance more expensive than a regular move. SQLite allows one writer at a time, so the app starts an immediate transaction before it reads the keys it needs to change.

The list shows 25 cars per page. I used Django’s built-in pagination for straightforward numbered pages. It uses an offset, so later pages can take more work for SQLite to retrieve.

## Database schema

The inventory uses one table, `cars_car`, with one row per car and no foreign keys.

- `id` is the primary key.
- `name` stores the car name, up to 100 characters.
- `color` stores the color name, up to 30 characters.
- `order_key` is a unique integer that determines where the car appears in the list.

The inventory uses one application table with one row per car. It has no foreign keys.

| Key or index | What it does |
| --- | --- |
| Primary key on `id` | Identifies the same car after an edit or a move. |
| Unique index on `order_key` | Gives each car a distinct position and supports reading the full list in order. |
| `car_color_order_idx` on `(color, order_key)` | Lets SQLite find cars of a given color and read them in list order. I confirmed that SQLite used it for the blue filter with `QuerySet.explain()`. |

### Normalization

- **1NF** — Each row holds one car, and each field holds a single value.
- **2NF** — Both candidate keys, `id` and `order_key`, are single columns, so there are no partial dependencies.
- **3NF** — `name` and `color` depend on the car’s key. Neither determines the other. The dependencies are `id → name, color, order_key` and `order_key → id, name, color`.

I kept `color` as text because the app only needs a color name for display and filtering. The add and edit forms offer five colors: Blue, Red, Silver, White, and Black. Django rejects any other value submitted through those forms. Repeating `blue` across several rows simply records that several cars are blue. If colors had shared details such as paint codes, I’d put those in a `Color` table and let many cars reference one color.

## Run the checks

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test
```

The 13 tests cover CRUD, form validation, missing records, filtered pagination, and ordering, including what happens when a gap runs out. Django runs them against a separate test database.