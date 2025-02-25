
class Prompts:

        target_prompt_right = ("""
        You will be given an image containing two columns with 24 evenly spaced rows. The right column is numbered 1 to 24 and is used only for reference. The left column contains the data you need to extract. Most rows contain handwritten text. The column does not have a header.

        **Instructions:**

        - Extract and list all numbers or the letter "x" from the left column. The "x" represents "N/A" or missing data.
        - Ensure your response contains exactly 24 entries, one per line.
        - Only include positive numbers and the letter "x" in your response—no other text or characters.
        - Double-check your list to confirm it has exactly 24 entries. If there are extra "x" characters, remove them to ensure the list is precise.
        - Do not prepend or append your response with any explanation—only respond with the extracted values.
        """)

        actual_prompt_right = ("""
        You will be given an image containing two columns with 24 evenly spaced rows. The right column is numbered 1 to 24 and is used only for reference. The left column contains the data you need to extract. Most rows contain handwritten text. The column does not have a header.

        **Instructions:**

        - Extract and list all numbers or the letter "x" from the left column. The "x" represents "N/A" or missing data.
        - Ensure your response contains exactly 24 entries, one per line.
        - Only include positive or numbers and the letter "x" in your response—no other text or characters.
        - Double-check your list to confirm it has exactly 24 entries. If there are extra "x" characters, remove them to ensure the list is precise.
        - Do not prepend or append your response with any explanation—only respond with the extracted values.
        """)

        delta_prompt_right = ("""
        You will be given an image containing two columns with 24 evenly spaced rows. The right column is numbered 1 to 24 and is used only for reference. The left column contains the data you need to extract. Most rows contain handwritten text. The column does not have a header.

        **Instructions:**

        - Extract and list all numbers or the letter "x" from the left column. The "x" represents "N/A" or missing data.
        - Ensure your response contains exactly 24 entries, one per line.
        - Only include positive or negative numbers and the letter "x" in your response—no other text or characters.
        - Double-check your list to confirm it has exactly 24 entries. If there are extra "x" characters, remove them to ensure the list is precise.
        - Do not prepend or append your response with any explanation—only respond with the extracted values.
        """)

        lost_prompt_right = ("""
        You will be given an image containing two columns with 24 evenly spaced rows. The right column is numbered 1 to 24 and is used only for reference. The left column contains the data you need to extract. It contains downtime codes representing each hour of the day. Most rows contain handwritten text. The column does not have a header.

        **Instructions:**

        - Entries in the left column are restricted to the following values: M1, M2, M3, M4, M5, M6, M7, Q1, Q2, D1, D2, D3, D4, D5, D6, and "x". The "x" signifies no issue during that hour.
        - Extract and list these values from top to bottom.
        - Ensure your response consists exclusively of 24 entries, each on a new line, corresponding to each row.
        - Respond solely with the values from the column, without adding any additional text or explanations.
        - Only provide the letters and numbers you read; no extraneous characters or formatting.
        """)

        notes_prompt_right = ("""
        You will be given an image containing two columns with 24 evenly spaced rows. The right column is numbered 1 to 24 and is used only for reference. The left column contains the data you need to extract. It contains miscellaneous notes from a "Day by the Hour" sheet used at a manufacturing site. Most rows contain handwritten text, but some may include machine-generated text. The column does not have a header.

        **Instructions:**

        - Focus on extracting text from each row of the column on the left from top to bottom.
        - Some rows may contain an "x", which indicates "N/A" or no specific note for that entry.
        - Ensure that your response consists of exactly 24 entries, each line corresponding to a row in the column.
        - The list should reflect the order of the rows in the image, with each entry as a separate line in your response.
        - Respond only with the text from each row, without adding any additional characters, formatting, or explanations.
        - Double-check your response to confirm that it includes exactly 24 entries, with no additional or missing information.
        """)

        target_prompt_left = ("""
        You will be given an image containing two columns with 24 evenly spaced rows. The left column is numbered 1 to 24 and is used only for reference. The right column contains the data you need to extract. Most rows contain handwritten text. The column does not have a header.

        **Instructions:**

        - Extract and list all numbers or the letter "x" from the right column. The "x" represents "N/A" or missing data.
        - Ensure your response contains exactly 24 entries, one per line.
        - Only include positive numbers and the letter "x" in your response—no other text or characters.
        - Double-check your list to confirm it has exactly 24 entries. If there are extra "x" characters, remove them to ensure the list is precise.
        - Do not prepend or append your response with any explanation—only respond with the extracted values.
        """)

        actual_prompt_left = ("""
        You will be given an image containing two columns with 24 evenly spaced rows. The left column is numbered 1 to 24 and is used only for reference. The right column contains the data you need to extract. Most rows contain handwritten text. The column does not have a header.

        **Instructions:**

        - Extract and list all numbers or the letter "x" from the right column. The "x" represents "N/A" or missing data.
        - Ensure your response contains exactly 24 entries, one per line.
        - Only include positive or numbers and the letter "x" in your response—no other text or characters.
        - Double-check your list to confirm it has exactly 24 entries. If there are extra "x" characters, remove them to ensure the list is precise.
        - Do not prepend or append your response with any explanation—only respond with the extracted values.
        """)

        delta_prompt_left = ("""
        You will be given an image containing two columns with 24 evenly spaced rows. The left column is numbered 1 to 24 and is used only for reference. The right column contains the data you need to extract. Most rows contain handwritten text. The column does not have a header.

        **Instructions:**

        - Extract and list all numbers or the letter "x" from the right column. The "x" represents "N/A" or missing data.
        - Ensure your response contains exactly 24 entries, one per line.
        - Only include positive or negative numbers and the letter "x" in your response—no other text or characters.
        - Double-check your list to confirm it has exactly 24 entries. If there are extra "x" characters, remove them to ensure the list is precise.
        - Do not prepend or append your response with any explanation—only respond with the extracted values.
        """)

        lost_prompt_left = ("""
        You will be given an image containing two columns with 24 evenly spaced rows. The left column is numbered 1 to 24 and is used only for reference. The right column contains the data you need to extract. It contains downtime codes representing each hour of the day. Most rows contain handwritten text. The column does not have a header.

        **Instructions:**

        - Entries in the right column are restricted to the following values: M1, M2, M3, M4, M5, M6, M7, Q1, Q2, D1, D2, D3, D4, D5, D6, and "x". The "x" signifies no issue during that hour.
        - Extract and list these values from top to bottom.
        - Ensure your response consists exclusively of 24 entries, each on a new line, corresponding to each row.
        - Respond solely with the values from the column, without adding any additional text or explanations.
        - Only provide the letters and numbers you read; no extraneous characters or formatting.
        """)

        notes_prompt_left = ("""
        You will be given an image containing two columns with 24 evenly spaced rows. The left column is numbered 1 to 24 and is used only for reference. The numbers in the left column are machine-generated text. The right column contains the data you need to extract. It contains miscellaneous notes from a "Day by the Hour" sheet used at a manufacturing site. Most text in the right column is handwritten text, but some text may be machine-generated. The column does not have a header.

        **Instructions:**

        - Focus on extracting text from each row of the column on the right from top to bottom.
        - Some rows may contain an "x", which indicates "N/A" or no specific note for that entry.
        - Ensure that your response consists of exactly 24 entries, each line corresponding to a row in the column.
        - The list should reflect the order of the rows in the image, with each entry as a separate line in your response.
        - Respond only with the text from each row from the column on the right, without adding any additional characters, formatting, or explanations.
        - Do not number the rows in your response.
        - Double-check your response to confirm that it includes exactly 24 entries, with no additional or missing information.
        """)
        