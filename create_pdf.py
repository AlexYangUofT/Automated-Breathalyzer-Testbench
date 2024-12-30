# Author: Alex Yang; Date: 2024-12
# This program is how to generate PDF file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import textwrap
from reportlab.lib.utils import ImageReader

def create_pdf(filename, tables, device_serial_number, completion_summary, previous_completed_tests, note, chart_filename = None):
    if not tables:
        print("No updates made, PDF not generated.")
        return

    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    left_margin = 50
    right_margin = width - 50
    y_position = height - 50  # Starting position from the top of each page

    # Function to draw device serial number, centered, with a line underneath on every page
    def draw_device_serial_number(c, y_position):
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(width / 2, y_position, f"Device Serial Number: {device_serial_number}")
        y_position -= 15
        # Thick separator line
        c.setLineWidth(1.5)
        c.line(left_margin, y_position, right_margin, y_position)
        return y_position - 20  # Adjust y_position for content below the line
    
    def draw_completed_tests_and_note(c, y_position, previous_completed_tests, note):
        if previous_completed_tests:
            c.setFont("Helvetica", 10)
            c.drawString(left_margin, y_position, f"Previously completed tests on the device number {device_serial_number}:")
            y_position -= 15
            for test in previous_completed_tests:
                c.drawString(left_margin, y_position, f"- {test}")
                y_position -= 12
            y_position -= 10
        if note: # Print the note if it exists
            c.setFont("Helvetica", 10)
            c.drawString(left_margin, y_position, "Note:")
            y_position -= 15  # Space after "Note:"
            # Justify the note text
            y_position = draw_justified_text(c, note, left_margin, y_position, right_margin - left_margin)
            y_position -= 10  # Additional spacing
        return y_position

    # Function to draw the completion summary only on the first page, below the thick line
    def draw_completion_summary(c, y_position, completion_summary):
        # Separate completed and pending messages
        if "The following tests are still pending:" in completion_summary:
            parts = completion_summary.split("The following tests are still pending:")
            completed_message = parts[0].strip()
            pending_message = "The following tests are still pending: " + parts[1].strip() if len(parts) > 1 else ""
        else:
            completed_message = completion_summary
            pending_message = ""

        # Draw the justified completion summary text, below the line
        c.setFont("Helvetica", 10)
        y_position = draw_justified_text(c, completed_message, left_margin, y_position, right_margin - left_margin)
        y_position -= 10 
        if pending_message:
            y_position = draw_justified_text(c, pending_message, left_margin, y_position, right_margin - left_margin)
        y_position -= 10
        return y_position

    # Function to draw justified text
    def draw_justified_text(c, text, x, y, max_width):
        words = text.split()
        lines = []
        current_line = []

        # Wrap lines manually
        for word in words:
            test_line = ' '.join(current_line + [word])
            if c.stringWidth(test_line, "Helvetica", 10) <= max_width:
                current_line.append(word)
            else:
                lines.append(current_line)
                current_line = [word]
        if current_line:
            lines.append(current_line)

        # Draw each line, justifying all except the last one
        for i, line_words in enumerate(lines):
            line_text = ' '.join(line_words)
            if i == len(lines) - 1:  # Last line: left-aligned
                c.drawString(x, y, line_text)
            else:  # Justified line
                line_width = c.stringWidth(line_text, "Helvetica", 10)
                extra_space = (max_width - line_width) / (len(line_words) - 1) if len(line_words) > 1 else 0
                x_offset = x
                for word in line_words[:-1]:
                    c.drawString(x_offset, y, word)
                    x_offset += c.stringWidth(word, "Helvetica", 10) + extra_space
                c.drawString(x_offset, y, line_words[-1])
            y -= 12
        return y

    # Draw serial number and completion summary on the first page
    y_position = draw_device_serial_number(c, y_position)
    y_position = draw_completed_tests_and_note(c, y_position, previous_completed_tests, note)
    y_position = draw_completion_summary(c, y_position, completion_summary)

    # Process each table and draw it
    for table in tables:
        # Check if a new page is needed for the next table
        if y_position < 40:
            c.showPage()
            y_position = height - 50
            y_position = draw_device_serial_number(c, y_position)  # Only device serial number on subsequent pages

        # Draw the table title centered
        table_title = table.get('title', 'Table')
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(width / 2, y_position, table_title)
        y_position -= 20

        # Define columns with more space for "User Entry"
        header_spacing = [left_margin, 180, 380, 500]  # X positions for columns
        column_widths = [header_spacing[i + 1] - header_spacing[i] for i in range(len(header_spacing) - 1)]
        column_widths.append(right_margin - header_spacing[-1])

        # Draw headers, centered within each column
        headers = ["Field", "Expected Results", "User Entry", "Status"]
        c.setFont("Helvetica-Bold", 10)
        for idx, header in enumerate(headers):
            c.drawString(header_spacing[idx] + column_widths[idx] / 2 - c.stringWidth(header, "Helvetica", 10) / 2, y_position, header)
        y_position -= 20  # Move down after headers

        # Draw each row with wrapping for "Field", "Expected Results", and "User Entry"
        c.setFont("Helvetica", 10)
        for field in table.get('fields', []):
            field_name = field.get("name", "")
            expected_result = field.get("expected_result", "")
            user_entry = field.get("user_entry", "")
            status = field.get("status", "")

            # Wrap the text in "Field" and "User Entry" to fit within the specified width
            wrapped_field_text = textwrap.wrap(field_name, width=40)  # Adjust width as necessary
            wrapped_expected_result = textwrap.wrap(expected_result, width=35)  # Added wrapping for expected results
            wrapped_user_entry = textwrap.wrap(user_entry, width=40)  # Adjust width as necessary

            # Calculate the total height needed for the tallest column in this row
            max_lines = max(len(wrapped_field_text), len(wrapped_user_entry), len(wrapped_expected_result))
            required_height = max_lines * 12

            # Check if there's enough space on the current page; if not, add a new page
            if y_position - required_height < 40:
                c.showPage()
                y_position = height - 50
                y_position = draw_device_serial_number(c, y_position)  # Only device serial number on subsequent pages

                # Redraw table title and headers on the new page
                c.setFont("Helvetica-Bold", 12)
                c.drawCentredString(width / 2, y_position, table_title)
                y_position -= 20
                c.setFont("Helvetica-Bold", 10)
                for idx, header in enumerate(headers):
                    c.drawString(header_spacing[idx] + column_widths[idx] / 2 - c.stringWidth(header, "Helvetica", 10) / 2, y_position, header)
                y_position -= 20

            # Draw each line for "Field" column, centered
            for i, line in enumerate(wrapped_field_text):
                field_name_x = header_spacing[0] + column_widths[0] / 2 - c.stringWidth(line, "Helvetica", 10) / 2
                c.drawString(field_name_x, y_position - i * 12, line)

            # Draw each line for "Expected Results", centered in its cell
            for i, line in enumerate(wrapped_expected_result):
                expected_x = header_spacing[1] + column_widths[1] / 2 - c.stringWidth(line, "Helvetica", 10) / 2
                c.drawString(expected_x, y_position - i * 12, line)

            # Draw each line for "User Entry" column, centered
            for i, line in enumerate(wrapped_user_entry):
                user_entry_x = header_spacing[2] + column_widths[2] / 2 - c.stringWidth(line, "Helvetica", 10) / 2
                c.drawString(user_entry_x, y_position - i * 12, line)

            # Draw "Status", centered in its cell
            status_x = header_spacing[3] + column_widths[3] / 2 - c.stringWidth(status, "Helvetica", 10) / 2
            c.drawString(status_x, y_position, status)

            # Move down by the height of the tallest column in the row
            y_position -= required_height + 10

    # Add the CO2 charts at the end of the PDF
    if chart_filename:  # chart_filename will now be a list of filenames
        for chart in chart_filename:
            try:
                c.showPage()  # Start a new page for each chart
                y_position = height - 50
                y_position = draw_device_serial_number(c, y_position)
                
                # Create a more readable title from the filename
                chart_title = (chart.replace('co2_sensor_', '')
                                  .replace('_chart.png', '')
                                  .replace('_', ' ')
                                  .title())
                
                # Special case for combined chart
                if 'combined' in chart_title.lower():
                    chart_title = 'Combined Graph Data'
                elif 'co2 flow' in chart_title.lower():
                    chart_title = 'CO2 Flow Data'
                elif 'return baseline' in chart_title.lower():
                    chart_title = 'Return Baseline Data'
                elif 'baseline' in chart_title.lower():
                    chart_title = 'Baseline Data'
                
                c.setFont("Helvetica-Bold", 14)
                c.drawCentredString(width / 2, y_position - 30, chart_title)
                
                # Verify file exists before attempting to draw
                import os
                if not os.path.exists(chart):
                    print(f"Warning: Chart file not found: {chart}")
                    continue
                
                # Draw the chart image centered on the page
                try:
                    img = ImageReader(chart)
                    c.drawImage(img, 
                              left_margin, 
                              y_position - 350,
                              width=right_margin - left_margin, 
                              height=300,
                              preserveAspectRatio=True)
                except Exception as e:
                    print(f"Error drawing chart {chart}: {e}")
                    print(f"Error details: {str(e)}")
                    
            except Exception as e:
                print(f"Error processing chart {chart}: {e}")
                continue

    c.save()
    print(f"PDF generated: {filename}")