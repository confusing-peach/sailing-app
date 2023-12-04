import sailing_app_info as info
import math as m 
import streamlit as st
import requests as r
import pandas as pd
import sympy as sp

#NEW
tab1, tab2, tab3 = st.tabs(["Forecasting", "VMGC Caclulator", "Sample VMGC Calculation"])

def sidebar():
    disclaimer = st.sidebar.expander("Disclaimer")
    disclaimer.subheader("Forecasting")
    disclaimer.write(info.forecasting_disclaimer)
    disclaimer.subheader("VMGC Calculator")
    disclaimer.write(info.vmgc_disclaimer)
    guide = st.sidebar.expander("Usage Guide")
    guide.subheader("Forecasting")
    guide.write(info.forecasting_guide)
    guide.subheader("VMGC Calculator")
    guide.write(info.vmgc_guide)
    about = st.sidebar.expander("About VMGC")
    about.write(info.vmgc_intro)
    process = st.sidebar.expander("How is VMGC normally calculated?")
    for bullet in (info.process):
        process.write(bullet)
    how = st.sidebar.expander("How does this app calculate VMGC?")
    for bullet in (info.how):
        how.write(bullet)
    limitations = st.sidebar.expander("VMGC Limitations")
    for bullet in (info.vmgc_limitations):
        limitations.write(bullet)
    goals = st.sidebar.expander("Future plans for this app")
    for bullet in (info.goals):
        goals.write(bullet)
    sources = st.sidebar.expander("Sources")
    for bullet in (info.sources):
        sources.write(bullet)
sidebar()

def forecast_backend(lat, long, minwind, maxwind):
    coords = str(lat) + "," + str(long) 
    full_url = info.finder_base_url + coords
    request_data = r.get(full_url)
    data = request_data.json()
    if data["type"] == info.unavailable or data["type"] == info.invalid:
        st.write("Unable to fetch forecast data. Please see sidebar for location limitations.")
        return None
    else:
        forecast_url = data["properties"]["forecastHourly"]
        forecast_request = r.get(forecast_url)
        forecast_data = forecast_request.json()
        forecast_dict = {}
        for aDict in forecast_data["properties"]["periods"]:
            start_time = aDict["startTime"]
            temp = aDict["temperature"]
            wind_speed = aDict["windSpeed"]
            wind_speed = wind_speed[:-4]
            wind_speed = int(wind_speed)
            in_range = wind_speed <= maxwind and wind_speed >= minwind
            wind_dir = aDict["windDirection"]
            if int(aDict["number"]) <= 24:
                forecast_dict[aDict["number"]] = (start_time, temp, wind_speed, in_range, wind_dir)
        time_list = []
        wind_actual_list = []
        wind_min_list = []
        wind_max_list = []
        temp_list= []
        for period, forecast in forecast_dict.items():
            wind_actual_list.append(forecast[2])
            temp_list.append(forecast[1])
            wind_min_list.append(minwind)
            wind_max_list.append(maxwind)
            time_list.append(period)
        wind_dict = {"Time (hours from now)": time_list, "Predicted speed (mph)": wind_actual_list, "Minimum speed (mph)": wind_min_list, "Maximum speed (mph)": wind_max_list}
        temp_dict = {"Time (hours from now)": time_list, "Temperature (F)": temp_list}
        temp_data = pd.DataFrame(temp_dict, columns = ["Time (hours from now)", "Temperature (F)"])
        wind_data = pd.DataFrame(wind_dict, columns = ["Time (hours from now)", "Predicted speed (mph)", "Minimum speed (mph)", "Maximum speed (mph)"])
        st.subheader("Temperature")
        # NEW
        st.line_chart(temp_data, x="Time (hours from now)", y="Temperature (F)")
        # NEW
        st.caption('This chart depicts temperature at the given coordinates at different times.')
        st.subheader("Wind")
        st.line_chart(wind_data, x="Time (hours from now)", y=["Predicted speed (mph)", "Minimum speed (mph)", "Maximum speed (mph)"], color=["#00FF00", "#FF0000", "#a2ddde"])
        st.caption('This chart depicts wind speed at the given coordinates at different times.')


def get_forecast_inputs():
    st.header("Sailing Forecast Generator")
    # NEW
    with st.form("forecast_form"):
        st.subheader("Select a location")
        st.write("Sample locations:")
        st.write("Georgia Tech: 33.7756° N, -84.3963° E")
        st.write("Lake Lanier Sailing Club: 34.2199° N, -83.9496° E")
        #NEW
        lat = st.number_input("Enter latitude", step = 0.0001)
        long = st.number_input("Enter longitude", step = 0.0001)
        #NEW
        st.divider()
        st.subheader("Select a windspeed limmits")
        minwind = st.number_input("Enter minimum windspeed in mph", step = 1, min_value= 0)
        maxwind = st.number_input("Enter maxmimum windspeed in mph", step = 1, min_value = 0)
        #NEW
        submit1 = st.form_submit_button("Get forecast!")
    if submit1:
        if maxwind < minwind:
            st.write("Error: Please input valid wind speeds")
            return None
        forecast_backend(lat, long, minwind, maxwind)
with tab1:
    get_forecast_inputs()

def path_find(dir1, dir2, cdir, clength):
    x1 = m.cos(m.radians(dir1))
    y1 = m.sin(m.radians(dir1))
    x2 = m.cos(m.radians(dir2))
    y2 = m.sin(m.radians(dir2))
    xc = m.cos(m.radians(cdir)) * clength
    yc = m.sin(m.radians(cdir)) * clength
    if dir1 != dir2:
        a = sp.Matrix([[x1,x2], [y1, y2]])
        b = sp.Matrix([xc, yc])
        sol, params = a.gauss_jordan_solve(b)
        len1 = sol[0] * m.sqrt(x1**2 + y1**2)
        len2 = sol[1] * m.sqrt(x1**2 + y1**2)
    else:
        len1 = clength
        len2 = clength
    return (len1, len2)

def vmgc_backend(course_dir, course_length, windspeed, wind_dir):
    relative_dir = (info.dir_dict[course_dir]-info.dir_dict[wind_dir]) % 360
    relative_dir_symb = info.rev_dir_dict[relative_dir]
    deg_offset = (relative_dir - info.dir_dict[course_dir]) %360
    head1_dir, head1_speed, head2_dir, head2_speed, default_speed = info.heading_data[windspeed][relative_dir_symb]
    head1_dir -= deg_offset
    head2_dir -= deg_offset
    head1_dir = round(head1_dir, 0) % 360
    head2_dir = round(head2_dir, 0) % 360
    head1_length, head2_length = path_find(head1_dir, head2_dir, relative_dir, course_length)
    head1_length = abs(round(head1_length, 1))
    head2_length = abs(round(head2_length, 1))
    head1_speed = round(head1_speed, 1)
    head2_speed = round(head2_speed, 1)
    opt_time = round((head1_length / head1_speed) + (head2_length / head2_speed), 1)
    default_time = round(course_length / default_speed, 1)
    time_saved = round(default_time - opt_time, 1)
    efficiency = round(abs((opt_time - default_time)/default_time) *100, 1)
    course_dir = info.dir_dict[course_dir]
    if head1_dir != head2_dir and default_time > opt_time :
        st.write("The first heading is {} degrees and will be followed at a speed of {} mph for {} miles.".format(head1_dir, head1_speed, head1_length))
        st.write("The second heading is {} degrees and will be followed at a speed of {} mph for {} miles.".format(head2_dir, head2_speed, head2_length))
        st.write("The caclulated course will take {} hours.".format(str(opt_time)))
        st.write("Sailing in a straight line will take {} hours.".format(str(default_time)))
        st.write("The calculated course saves {} hours!".format(str(time_saved)))
        st.write("That's {}% faster!".format(str(efficiency)))
    else:
        st.write("The fastest approach is to sail straight, without tacking.")
        st.write("Sail {} miles at a heading of {} degrees and a speed of {} mph to reach your destination in {} hours.".format(str(course_length), str(course_dir), str(default_speed), str(default_time)))

def get_vmgc_inputs():
    st.divider()
    st.header("Velocity Made Good on Course Calculator")
    st.write(info.vmgc_instructions1)
    st.write(info.vmgc_instructions2)
    with st.form("vmgc_form"):
        st.subheader("Select a location")
        st.write("Sample locations:")
        st.write("Georgia Tech: 33.7756° N, -84.3963° E")
        st.write("Lake Lanier Sailing Club: 34.2199° N, -83.9496° E")
        startlat = st.number_input("Enter starting latitude", step = 0.0001)
        startlong = st.number_input("Enter starting longitude", step = 0.0001)
        st.divider()
        st.subheader("Enter course information")
        #NEW
        course_dir = st.selectbox("Select course direction", ["N","NNE", "NE","ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"])
        course_length = st.number_input("Enter course length in miles", min_value=0.1)
        st.divider()
        st.subheader("Enter wind information")
        st.write("Wind information is optional if you entered a location within the bounds of the NWS' predictions. See sidebar for more information.")
        windspeed = st.number_input("Enter windspeed in knots", step = 1, min_value= 0)
        wind_dir = st.selectbox("Select wind direction", ["N","NNE", "NE","ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"])
        submit2 = st.form_submit_button("Plot VMGC optimization!")
    if submit2:
        windspeed = int(windspeed)
        est_wind = windspeed
        if course_length == 0:
            st.write("You must travel at least 0.1 miles")
            return None
        if windspeed == 0:
            coords = str(startlat) + "," + str(startlong) 
            full_url = info.finder_base_url + coords
            request_data = r.get(full_url)
            data = request_data.json()
            if data["type"] == info.unavailable or data["type"] == info.invalid:
                st.write("Unable to fetch forecast data. Please see sidebar for location limitations or manually input wind speed and direction.")
                return None
            forecast_url = data["properties"]["forecastHourly"]
            forecast_request = r.get(forecast_url)
            forecast_data = forecast_request.json()
            windspeed = forecast_data["properties"]["periods"][1]["windSpeed"]
            windspeed = windspeed[:-4]
            windspeed = int(windspeed)
            windspeed = windspeed / 1.151
            dir_data = forecast_data["properties"]["periods"][1]["windDirection"]
            if windspeed <= 7:
                est_wind = 6
            elif windspeed <= 9:
                est_wind = 8
            elif windspeed <= 11:
                est_wind = 10
            elif windspeed <= 13:
                est_wind = 12
            elif windspeed <= 15:
                est_wind = 14
            elif windspeed <= 18:
                est_wind = 16
            elif windspeed > 18:
                est_wind = 20
        vmgc_backend(course_dir, course_length, est_wind, wind_dir)

with tab2:
    get_vmgc_inputs()

def sample_vmgc():
    st.header("Sample VMGC calculation")
    st.write(info.prologue)
    st.write(info.step1)
    st.image("sailing_app/sailing_app_images/image1.png")
    st.caption("6-knot VMG dataset for the J-24")
    st.write(info.step2)
    # NEW
    st.latex(info.step2l)
    st.write(info.step3)
    st.image("sailing_app/sailing_app_images/image2.png")
    st.caption("Curve fit parameters")
    st.image("sailing_app/sailing_app_images/image3.png")
    st.caption("Curve fit (grey line) and points fitted (red points)")
    st.write(info.step4)
    st.latex(info.step4l)
    st.latex(info.step4l2)
    st.write(info.step5)
    st.latex(info.step5l1)
    st.latex(info.step5l2)
    st.write(info.step6)
    st.latex(info.step6l)
    st.image("sailing_app/sailing_app_images/image4.png")
    st.caption("Polar graph with the blue line pointing to the course")
    st.write(info.step7)
    st.latex(info.step7l)
    st.image("sailing_app/sailing_app_images/image5.png")
    st.caption("Polar graph with the blue line pointing to the course and dashed blue line as the perpendicular line to the course")
    st.write(info.step8)
    st.latex(info.step8l)
    st.caption("Solving this equation is very difficult - so difficult that as far as I know, only desmos is capable of solving it. This is why the app currently only supports a small number of directions.")
    st.write(info.step9)
    st.latex(info.step9l1)
    st.caption("Equation of the tangent line.")
    st.latex(info.step9l2)
    st.caption("Equation of the heading line")
    st.image("sailing_app/sailing_app_images/image6.png")
    st.caption("Green line is the heading. Green dotted line is the tangent.")
    st.write(info.step10)
    st.latex(info.step10l1)
    st.caption("Solving the Euler approximation to find the tangent location.")
    st.latex(info.step10l2)
    st.caption("Equation for the tangent.")
    st.latex(info.step10l3)
    st.caption("Equation for the line to the second heading")
    st.image("sailing_app/sailing_app_images/image7.png")
    st.caption("Red solid line is the second heading. Red dotted line is the tangent.")
    st.write(info.step11)
    st.latex(info.step11l1)
    st.caption("Finding the measure in degrees of the first heading")
    st.latex(info.step11l2)
    st.caption("Finding the measure in degrees of the second heading")
    st.write(info.step12)
    st.latex(info.step12l1)
    st.caption("Finding speed at course angle")
    st.latex(info.step12l2)
    st.caption("Converting to mph")
    st.latex(info.step12l3)
    st.caption("Finding the time in hours")
    st.write(info.step13)
    st.latex(info.step13l1)
    st.caption("Finding speed on first heading")
    st.latex(info.step13l2)
    st.caption("Finding speed on second heading")
    st.write(info.step14)
    st.latex(info.step14l1)
    st.caption("First heading vector.")
    st.latex(info.step14l2)
    st.caption("Second heading vector.")
    st.latex(info.step14l3)
    st.caption("Course vector.")
    st.latex(info.step14l4)
    st.caption("Matrix to solve.")
    st.latex(info.step14l5)
    st.caption("The solved matrix.")
    st.write(info.step15)
    st.latex(info.step15l1)
    st.caption("Finding the time on the first heading.")
    st.latex(info.step15l2)
    st.caption("Finding the time on the second heading.")
    st.latex(info.step15l3)
    st.caption("Finding the total time.")
    st.write(info.step16)
    st.write(info.epilogue)
with tab3:
    sample_vmgc()