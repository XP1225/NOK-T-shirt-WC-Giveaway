from flask import Flask, render_template_string, request, jsonify
import pandas as pd
import threading

# Initialize Flask app
app = Flask(__name__)

# Load data from Excel
file_path = 'NJ_Murray Hill_giveaway_2024_og.xlsx'
name_list_df = pd.read_excel(file_path, sheet_name='Name List')
inventory_df = pd.read_excel(file_path, sheet_name='Purchased')
log_df = pd.read_excel(file_path, sheet_name='Saved Data')

# HTML content for entry_form.html (in the same folder as app.py)
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Employee Entry Form</title>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
</head>
<body>
    <h1>Employee Entry Form: T-Shirt Size & Color</h1>
    <form method="POST">
        <label for="id_input">ID #:</label>
        <input type="text" id="id_input" name="id_input" required>
        <br><br>
        
        <label for="name">Name:</label>
        <input type="text" id="name" name="name" readonly>
        <br><br>
        
        <label for="org">Org:</label>
        <input type="text" id="org" name="org" readonly>
        <br><br>

        <label for="eligibility_status">Eligible:</label>
        <input type="text" name="eligibility_status" value="{{ eligibility_status }}" readonly><br><br>

        <label for="size_input">T-Shirt Size:</label>
        <select id="size_input" name="size_input">
            <option value="">-- Select Size --</option> <!-- Blank option -->
            <option value="XS">XS</option>
            <option value="S">S</option>
            <option value="M">M</option>
            <option value="L">L</option>
            <option value="XL">XL</option>
            <option value="2X">2X</option>
            <option value="Declined">Declined</option> <!-- Added option -->
        </select>
        <br><br>
        
        <label for="color_input">Color:</label>
        <select id="color_input" name="color_input">
            <option value="">-- Select Color --</option> <!-- Blank option -->
            <option value="Black">Black</option>
            <option value="Blue">Blue</option>
            <option value="Green">Green</option>
            <option value="Orange">Orange</option>
            <option value="Purple">Purple</option>
            <option value="Red">Red</option>
            <option value="Yellow">Yellow</option>
            <option value="Declined">Declined</option> <!-- Added option -->
        </select>
        <br><br>
        
        <label for="stock_info">Stock Info:</label>
        <input type="text" id="stock_info" name="stock_info" readonly>
        <br><br>
        
        <label for="comments">Comments:</label>
        <textarea name="comments"></textarea>
        <br><br>
        
        <label for="operator_name">Entered by:</label>
        <select id="operator_name" name="operator_name" required>
            <option value="SteveB">SteveB</option>
            <option value="XiaoP">XiaoP</option>
            <option value="StacyK">StacyK</option>
            <option value="DebB">DebB</option>
            <option value="SueW">SueW</option>
            <option value="LauraK">LauraK</option>
            <option value="ChrisO">ChrisO</option>
            <option value="AmyC">AmyC</option>
            <option value="Other">Other</option> <!-- Added as per usual options -->
        </select>
        <br><br>
        
        <button type="submit" name="submit">Submit</button>
    </form>
    
    <p id="message">{{ message }}</p>
    
    <script>
        $(document).ready(function() {
            // Update name, org, and eligibility status when ID is entered
            $('#id_input').on('input', function() {
                let id = $(this).val();
                if (id) {
                    $.ajax({
                        type: 'POST',
                        url: '/get_employee_info',
                        contentType: 'application/json',
                        data: JSON.stringify({ id: id }),
                        success: function(response) {
                            $('#name').val(response.name);
                            $('#org').val(response.org);
                            $('input[name="eligibility_status"]').val(response.eligibility_status);
                        }
                    });
                } else {
                    // Clear fields if input is cleared
                    $('#name').val('');
                    $('#org').val('');
                    $('input[name="eligibility_status"]').val('');
                }
            });
        });
    </script>

</body>
</html>
"""

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
                return render_template_string(html_template, employee_info=employee_info, org_info=org_info, stock_info=stock_info, eligibility_status=eligibility_status, message=message)

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

    return render_template_string(html_template, employee_info=employee_info, org_info=org_info, stock_info=stock_info, eligibility_status=eligibility_status, message=message)

# Run Flask app
if __name__ == '__main__':
    def run_app():
        app.run(host='0.0.0.0', debug=True, use_reloader=False)

    threading.Thread(target=run_app).start()

