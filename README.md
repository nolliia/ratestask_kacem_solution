## Ratestask

## Getting started

- Install PostgreSQL if not already installed
- Login to psql `psql postgres -U yourusername`
- Create a database with any name of your choice `create database name`
- Logout of psql and make sure `rates.sql` is in the current directory
- Populate the databse you just created `psql db_name < rates.sql`
- In the `.env` file, change database credentials to match yours
- Start the server by running the script `python app.py`. The app runs on localhost on port 5000

# Routes

The API has just one route
**`GET '/rates'`**

The route accepts 4 query parameters and cannot work without any of them

- `date_from`: Date (format "YYYY-MM-DD")
- `date_to`: Date (format "YYYY-MM-DD")
- `origin`: 5 character code or region name
- `destination`: 5 character code or region name

**Sample requests**

```insomnia or browser
  http://127.0.0.1:5000/rates?date_from=2016-01-01&date_to=2016-01-10&origin=GBLON&destination=DEHAM
  http://127.0.0.1:5000/rates?date_from=2016-01-01&date_to=2016-01-10&origin=CNGGZ&destination=NOKRS
```

```bash
  curl http://127.0.0.1:5000/rates?date_from=2016-01-01&date_to=2016-01-10&origin=CNSGH&destination=north_europe_main
```

```json
    [
        {
            "day": "2016-01-01",
            "average_price": 1112
        },
        {
            "day": "2016-01-02",
            "average_price": 1112
        },
        {
            "day": "2016-01-03",
            "average_price": null
        },
        ...
    ]
```

- If any or all of the query parameters are missing, it returns a bad request error.
- If either the origin or destination entered is not found in the database, it returns a not found error.
- Both origin and destination could be regions
- I didn't create a class with multiple functions as we only have one request which is get if I had other things I would have created a class and implement a a path or a delete method
- also I took in consideration the prices if they are < 3 and also the destination and the origin are the same to add to that as the number are intergers I rounded up the average_price
# ratestask_kacem_solution
