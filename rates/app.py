from flask import Flask, jsonify, request, abort
import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()  # load vales in .env file to environment variables


app = Flask(__name__)

app.config['JSON_SORT_KEYS'] = False # so the dates will be first and then the prices and not the other way around
db_name = os.getenv("DB_NAME")
dbpassword = os.getenv("DB_PASSWORD")
dbuser = os.getenv("DB_USER")

connection = psycopg2.connect(f"dbname={db_name} user={dbuser} password={dbpassword}")

cursor = connection.cursor()

# API Routes-------
@app.route("/rates")
def rates():
    if not request.args:
        abort(400)  # if no query params, abort as a bad request

    get_date_from = request.args.get("date_from")
    get_date_to = request.args.get("date_to")
    get_origin = request.args.get("origin")
    get_destination = request.args.get("destination")

    if not get_date_from or not get_date_to or not get_origin or not get_destination:
        abort(400)  # if any query param is missing, abort as a bad request

    origin = {
        "value": get_origin,
        "region": False,  # if given origin is a region or a port
    }
    destination = {
        "value": get_destination,
        "region": False,  # if given destination is a region or port
    }
    date_from = datetime.strptime(get_date_from, "%Y-%m-%d")
    date_to = datetime.strptime(get_date_to, "%Y-%m-%d")

    # check for origin
    cursor.execute(f"SELECT * FROM ports WHERE code = '{get_origin}';")

    port = cursor.fetchone()
    if port is None:  # if not found on port table, check if it's a region slug
        cursor.execute(f"SELECT * FROM regions WHERE slug = '{get_origin}';")
        region = cursor.fetchone()
        if region is None:
            abort(404)  # specified origin not found in database
        elif region:
            origin["region"] = True
        elif port:
            origin["region"] = False

    # check destination
    cursor.execute(f"SELECT * FROM ports WHERE code = '{get_destination}';")

    port = cursor.fetchone()
    if port is None:  # if not found on port table, check if it's a region slug
        cursor.execute(f"SELECT * FROM regions WHERE slug = '{get_destination}';")
        region = cursor.fetchone()
        if region is None:
            abort(404)  # specified origin not found in database
        elif region:
            destination["region"] = True
        elif port:
            destination["region"] = False

    number_of_days = date_to - date_from
    days = [
        date_from.date() + timedelta(days=day) for day in range(number_of_days.days + 1)
    ]
    days = [day.strftime("%Y-%m-%d") for day in days]  # format dates
    prices = []

    if (
        not origin["region"] and not destination["region"]
    ):  # origin and destination are ports
        for day in days:
            daily_prices = []
            # query prices with origin, destination and day for price
            cursor.execute(
                f"""SELECT price FROM prices 
                    WHERE orig_code = '{origin['value']}' 
                    AND dest_code = '{destination['value']}' 
                    AND "day" = to_date(to_char({day.replace("-", "")}, '99999999'), 'YYYYMMDD');
                """
            )
            daily_price = cursor.fetchall()
            if len(daily_price) >= 3:
                # append to daily_prices
                for price in daily_price:
                    daily_prices.append([price][0][0])
                # calculate average and append to prices
                average_price = round(sum(daily_prices) / len(daily_prices) )
                prices.append({"day": day, "average_price": average_price})
            else:
                prices.append({"day": day, "average_price": None})

    elif (
        origin["region"] and not destination["region"]
    ):  # origin is a region and destination is a port
        parent_slugs = [] # list of all sub regions and region

        # query for sub regions
        cursor.execute(
            f"SELECT slug FROM regions WHERE parent_slug = '{origin['value']}';"
        )
        regions = cursor.fetchall()

        if regions:
            for region in regions: # get port codes of each sub region
                parent_slugs.append([region][0][0])
            parent_slugs.append(origin["value"]) # finially add the given destination slug
        else:
            parent_slugs.append(origin['value'])

        origin_ports = []
        for parent_slug in parent_slugs: # query for destination ports with slug and append to destination_ports
            cursor.execute(
                f"SELECT code FROM ports WHERE parent_slug = '{parent_slug}';"
            )
            port_codes = cursor.fetchall()
            for port_code in port_codes:
                origin_ports.append([port_code][0])

        for day in days:
            daily_prices = []
            for ports in origin_ports:
                # query prices with origin, destination AND "day" for price
                cursor.execute(
                    f"""SELECT price FROM prices 
                        WHERE orig_code = '{ports[0]}' 
                        AND dest_code = '{destination['value']}' 
                        AND "day" = to_date(to_char({day.replace("-", "")}, '99999999'), 'YYYYMMDD');
                    """
                )
                daily_price = cursor.fetchall()
                if len(daily_price) >= 3:
                    # append to daily_prices
                    for price in daily_price:
                        daily_prices.append([price][0][0])
            if daily_prices:
                # calculate average and append to prices
                average_price = round(sum(daily_prices) / len(daily_prices))
                prices.append({"day": day, "average_price": average_price})
            else:
                prices.append({"day": day, "average_price": None})

    elif (
        not origin["region"] and destination["region"]
    ):  # origin is a port and destination is a region
        parent_slugs = [] # list of all sub regions and region

        # query for sub regions
        cursor.execute(
            f"SELECT slug FROM regions WHERE parent_slug = '{destination['value']}';"
        )
        regions = cursor.fetchall()

        if regions:
            for region in regions: # get port codes of each sub region
                parent_slugs.append([region][0][0])
            parent_slugs.append(destination["value"]) # finially add the given destination slug
        else:
            parent_slugs.append(destination['value'])

        destination_ports = []
        for parent_slug in parent_slugs: # query for destination ports with slug and append to destination_ports
            cursor.execute(
                f"SELECT code FROM ports WHERE parent_slug = '{parent_slug}';"
            )
            port_codes = cursor.fetchall()
            for port_code in port_codes:
                destination_ports.append([port_code][0])
        
        for day in days:
            daily_prices = []
            for ports in destination_ports:
                # query prices with origin, destination and day for price
                cursor.execute(
                    f"""SELECT price FROM prices 
                        WHERE orig_code = '{origin['value']}' 
                        AND dest_code = '{ports[0]}' 
                        AND "day" = to_date(to_char({day.replace("-", "")}, '99999999'), 'YYYYMMDD');
                    """
                )
                daily_price = cursor.fetchall()
                if len(daily_price) >= 3:

                    # append to daily_prices
                    for price in daily_price:
                        daily_prices.append([price][0][0])
            if daily_prices:
                # calculate average and append to prices
                average_price = round(sum(daily_prices) / len(daily_prices))
                prices.append({"day": day, "average_price": average_price})
            else:
                prices.append({"day": day, "average_price": None})

    elif (
        origin["region"] and destination["region"]
    ):  # origin and destination are regions
        origin_parent_slugs = [] # list of all sub regions and region of origin

        # query for sub regions
        cursor.execute(
            f"SELECT slug FROM regions WHERE parent_slug = '{origin['value']}';"
        )
        regions = cursor.fetchall()

        if regions:
            for region in regions: # get port codes of each sub region
                origin_parent_slugs.append([region][0][0])
            origin_parent_slugs.append(origin["value"]) # finially add the given destination slug
        else:
            origin_parent_slugs.append(origin['value'])

        origin_ports = []
        for parent_slug in origin_parent_slugs: # query for destination ports with slug and append to destination_ports
            cursor.execute(
                f"SELECT code FROM ports WHERE parent_slug = '{parent_slug}';"
            )
            port_codes = cursor.fetchall()
            for port_code in port_codes:
                origin_ports.append([port_code][0])

        destination_parent_slugs = [] # list of all sub regions and region of destination

        # query for sub regions
        cursor.execute(
            f"SELECT slug FROM regions WHERE parent_slug = '{destination['value']}';"
        )
        regions = cursor.fetchall()

        if regions:
            for region in regions: # get port codes of each sub region
                destination_parent_slugs.append([region][0][0])
            destination_parent_slugs.append(destination["value"]) # finially add the given destination slug
        else:
            destination_parent_slugs.append(destination['value'])

        destination_ports = []
        for parent_slug in parent_slugs: # query for destination ports with slug and append to destination_ports
            cursor.execute(
                f"SELECT code FROM ports WHERE parent_slug = '{parent_slug}';"
            )
            port_codes = cursor.fetchall()
            for port_code in port_codes:
                destination_ports.append([port_code][0])

        for day in days:
            # nested loop with length of origin and destination ports to get all corresponding prices
            daily_prices = []
            outer_loop = (
                len(origin_ports)
                if len(origin_ports) > len(destination_ports)
                else len(destination_ports)
            )
            inner_loop = (
                len(destination_ports)
                if len(destination_ports) < len(origin_ports)
                else len(origin_ports)
            )
            for i in range(outer_loop):
                for j in range(inner_loop):
                    # query origin, destination and day for price
                    cursor.execute(
                        f"""SELECT price FROM prices 
                            WHERE orig_code = '{(
                                destination_ports[j][0] 
                                if inner_loop == len(destination_ports) 
                                else origin_ports[j][0]
                            )}' 
                            AND dest_code = '{(
                                origin_ports[i][0]
                                if outer_loop == len(origin_ports) 
                                else destination_ports[i][0]
                            )}' 
                            AND "day" = to_date(to_char({day.replace("-", "")}, '99999999'), 'YYYYMMDD');
                        """
                    )
                    daily_price = cursor.fetchall()
                    if len(daily_price) >= 3:
                        # append to daily_prices
                        for price in daily_price:
                            daily_prices.append([price][0][0])
            if daily_prices:
                # calculate average and append to prices
                average_price = round(sum(daily_prices) / len(daily_prices))
                prices.append({"day": day, "average_price": average_price})
            else:
                prices.append({"day": day, "average_price": None})

    return jsonify(prices)


if __name__ == "__main__":
    app.run(debug=True)
