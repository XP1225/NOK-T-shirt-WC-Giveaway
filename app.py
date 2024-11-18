from flask import Flask, render_template, request, jsonify
import pandas as pd
import threading

# Initialize Flask app
app = Flask(__name__, template_folder='templates')

# Load data from Excel (update the path to match your GitHub repository structure)
file_path = 'NOK-T-shirt-WC-Giveaway/NJ_Murray Hill_giveaway_2024_og.xlsx'
name_list_df = pd.read_excel(file_path, sheet_name='Name List')
inventory_df = pd.read_excel(file_path, sheet_name='Purchased')
log_df = pd.read_excel(file_path, sheet_name='Saved Data')

@app.route('/', methods=['GET', 'POST'])
def entry_form():
    global log_df, inventory_df, name_list_df  # Declare global variables

    employee_info = None
    org_info = None
    stock_info = ""
    eligibility_status = ""
    message = ""

    # Check for GET request to pre-fill the eligibility status based on input ID
    if request.method == 'GET':
        employee_id = request.args.get('id_input')
        if employee_id:
            try:
                employee_id = int(employee_id)
                # Find the employee in the name list
                employee_info_row = name_list_df[name_list_df['Nokia ID'] == employee_id]
                if not employee_info_row.empty:
                    employee_info = employee_info_row.iloc[0]['MH Employee Name']
                    org_info = employee_info_row.iloc[0]['Org']
                    t_shirt_qty = employee_info_row.iloc[0]['T-Shirt Qty']

                    # Check eligibility based on 'T-Shirt Qty'
                    if pd.isna(t_shirt_qty) or t_shirt_qty == 0:
                        eligibility_status = "Yes"  # Eligible if not picked up or Qty is 0
                    else:
                        eligibility_status = "No"  # Not eligible if Qty is already 1 or not blank
                else:
                    employee_info = "Not Found"
                    org_info = "N/A"
                    eligibility_status = "N/A"
            except ValueError:
                message = "Invalid ID format. Please enter a valid number."

    # Handle POST request for submission
    if request.method == 'POST':
        # Get the form data
        employee_id = request.form.get('id_input')
        size_input = request.form.get('size_input')
        color_input = request.form.get('color_input')
        operator_name = request.form.get('operator_name')
        comments = request.form.get('comments')

        try:
            employee_id = int(employee_id)
            # Find the employee in the name list
            employee_info_row = name_list_df[name_list_df['Nokia ID'] == employee_id]
            if not employee_info_row.empty:
                employee_info = employee_info_row.iloc[0]['MH Employee Name']
                org_info = employee_info_row.iloc[0]['Org']
                t_shirt_qty = employee_info_row.iloc[0]['T-Shirt Qty']

                # Check eligibility based on 'T-Shirt Qty'
                if pd.isna(t_shirt_qty) or t_shirt_qty == 0:
                    eligibility_status = "Yes"  # Eligible if not picked up or Qty is 0
                else:
                    eligibility_status = "No"  # Not eligible if Qty is already 1 or not blank
            else:
                employee_info = "Not Found"
                org_info = "N/A"
                eligibility_status = "N/A"
                message = "Error: Invalid employee ID."
                return render_template('entry_form.html', employee_info=employee_info, org_info=org_info, stock_info=stock_info, eligibility_status=eligibility_status, message=message)

            # Check stock and record submission
            if size_input and color_input:
                current_stock = inventory_df.loc[inventory_df['Color/Size'] == color_input, size_input].values[0]
                if current_stock > 0:
                    stock_info = f"{current_stock} in stock"
                else:
                    stock_info = "Out of Stock"

                # Update inventory and log data only if the selection is valid and not 'Declined'
                if color_input != "Declined" and size_input != "Declined":
                    inventory_df.loc[inventory_df['Color/Size'] == color_input, size_input] -= 1
                    size_qty = 1
                else:
                    size_qty = 0

                # Record the data in the Name List sheet
                name_list_df.loc[name_list_df['Nokia ID'] == employee_id, ['T-Shirt Size', 'T-Shirt Color', 'T-Shirt Qty', 'Logged by (Initials)']] = [size_input, color_input, size_qty, operator_name]

                # Add entry to log_df
                new_entry = {
                    'Nokia ID': employee_id,
                    'Employee Name': employee_info,
                    'Org': org_info,
                    'T-Shirt Size': size_input,
                    'T-Shirt Color': color_input,
                    'Comments': comments,
                    'Operator': operator_name
                }
                log_df = pd.concat([log_df, pd.DataFrame([new_entry])], ignore_index=True)

                # Save changes back to Excel
                with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    name_list_df.to_excel(writer, sheet_name='Name List', index=False)
                    inventory_df.to_excel(writer, sheet_name='Purchased', index=False)
                    log_df.to_excel(writer, sheet_name='Saved Data', index=False)

                message = "Entry submitted successfully!"
            else:
                message = "Error: Please select both size and color."

        except ValueError:
            message = "Invalid ID format. Please enter a valid number."

    return render_template('entry_form.html', employee_info=employee_info, org_info=org_info, stock_info=stock_info, eligibility_status=eligibility_status, message=message)

# Run Flask app
if __name__ == '__main__':
    def run_app():
        app.run(host='0.0.0.0', debug=True, use_reloader=False)

    threading.Thread(target=run_app).start()
