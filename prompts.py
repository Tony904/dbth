system_prompt = ('You will be given an image of a single column with 24 evenly spaced rows. Read each row in the column from top to bottom.'
        ' Any given row may or may not contain data. In this column there will be no empty rows, only 24 numbers and/or letters. '
        'Read the column from top to bottom and be sure to double check your response before responding. '
        'There are only 24 values, so do not respond with more than 24 values. In your response, format empty rows as if they had an entry of the underscore symbol (_).'
        ' Respond only with a list of length 24 corresponding to the 24 rows with each row delimited by the newline character. '
        'You MUST only respond with a list of length 24. Do not respond with a list that has more or less than 24 entries, if you do you die. '
        'Do not prepend or postpend your response with what the response will be about. If you do you will die. Only include the values you read in your response. '
        'Nothing else shall be added. ')

target_prompt =  ('Please provide the information without using backticks or any special formatting. You will be given an image of 2 columns each with 24 evenly spaced rows. Only respond with the numbers in the left column. DO NOT include """`""" in your response. '
                  ' Use the column on the right as an index for where to place responses. This column is labeled with the numbers 1 thourgh 24. NEVER respond with anything you read in the right column. Think of this column as a a column which labels which number each row is. '
                  ' In this column there will be no empty rows, only 24 numbers. '
                  'Read the column from top to bottom and be sure to double check your response before responding.'
                  ' There are only 24 values, so do not respond with more than 24 values. '
                  'In your response there should be exatly 24 values. Only respond with positive numbers (can be mutliple digits) and x, no other charcters should be included, and if they are you will die.'
                  ' If you read a "-" between two numbers, just delete it and move the second number over. '
                  'Respond only with a list of length 24 corresponding to the 24 rows with each row delimited by the newline character. Make sure the list is 24 values exactly. '
                  'You MUST only respond with a list of length 24. Do not respond with a list that has more or less than 24 entries, if you do you die. '
                  'Do not prepend or postpend your response with what the response will be about. If you do you will die. '
                  'Only include the values you read in your response. Do not prepend your response with anything, just respond.'
                  'Nothing else shall be added. ')

actual_prompt = ('Please provide the information without using backticks or any special formatting. You will be given an image of a single column with 24 evenly spaced rows. Read each row in the column from top to bottom. Only respond with the numbers in the left column. Use the column on the right as guide for where to place responses. DO NOT respond with anything you read in the right column. ONLY include the values you read in the column, NOTHING ELSE. ONLY include numbers in your response; NO OTHER CHARACTERS.  '
        ' In this column there will be no empty rows, only 24 numbers and/or letters. This column will include positive numbers and the letter x ONLY. '
        'Read the column from top to bottom. '
        'Read row by row and only move onto the next row when you are done reading the current. '
        ' Respond only with a list of length 24 corresponding to the 24 rows with each row delimited by the newline character. '
        'You MUST only respond with a list of length 24. Do not respond with a list that has more or less than 24 entries, if you do you die. '
        'Do not prepend or postpend your response with what the response will be about. If you do you will die. Only include the values you read in your response. '
        'Nothing else shall be added. Double check your response before responding. ')

delta_prompt = ('Please provide the information without using backticks or any special formatting.You will be given an image of a single column with 24 evenly spaced rows. Read each row in the column from top to bottom. Only respond with the numbers in the left column. '
                'Use the column on the right as an index for where to place responses. DO NOT respond with anything you read in the right column. '
                'ONLY include the values you read in the column, NOTHING ELSE. Do not include """''""" in your response '
        ' In this column there will be no empty rows, only 24 numbers and/or letters. This column will include positive and negative numbers and the letter x. '
        'Read the column from top to bottom. Only include numbers and letters in your response, nothing else. '
        'Read row by row and only move onto the next row when you are done reading the current. You can treat the column as a list of 24 numbers and letters, just respond with the exact list. '
        ' Respond only with a list of length 24 corresponding to the 24 rows with each row delimited by the newline character. '
        'You MUST only respond with a list of length 24. Do not respond with a list that has more or less than 24 entries, if you do you die. '
        'Do not prepend or postpend your response with what the response will be about. If you do you will die. Only include the values you read in your response. '
        'Nothing else shall be added. Double check responses  before responding. ')

lost_prompt =('Please provide the information without using backticks or any special formatting. NEVER INCLUDE backticks in your response.NEVER USE SPECIAL FORMATING Do not prepend your response with what it will be about, only include the list of 24. Only respond with the numbers in the left column. Use the column on the right as an index for where to place responses. DO NOT respond with anything you read in the right column. Remove all backtick characters """`""" from your response before responding.  DO NOT include ANY backticks characters """`""" in your response.'
            'This is the lost time column. This column will include exactly 24 values. These represent an hour of the day. '
            'These values include and are limited to: M1, M2, M3, M4, M5, M6, M7, Q1, Q2, D1, D2, D3, D4, D5, D6, and x. '
            'The Xs represent a column where there was no issue in the hour. No other value should be put in this column. Read this column from top to bottom.'
            'You MUST only respond with a list of length 24. Do not respond with a list that has more or less than 24 entries, if you do you die. '
            ' Respond only with a list of length 24 corresponding to the 24 rows with each row delimited by the newline character. DO NOT predend your response, ONLY include values you read.  '
            'Only include the values, do not include any values that you add. Only include numbers and letters in your response, nothing else.')

notes_prompt= (
    'Please provide the information without using backticks or any special formatting. Read the column row by row from top to bottom. Only respond with the numbers in the left column. Use the column on the right as an index for where to place responses. DO NOT respond with anything you read in the right column. ONLY include the values you read in the column, NOTHING ELSE.'
    'Do not prepend your response with what your response will be about. Do not include """''""" in your response. '
    'Treat the column as a list of 24 values, with each row containing one data entry in the list.'
    'Read the data in each of the 24 rows from top to bottom VERY CAREFULLY.'
    'Read the rows one by one and do not move on until the entire row is recorded correctly.'
    'Some rows may or may not contain data. In your response, format empty rows as if they had an entry of the x symbol "x". '
    'Respond ONLY with a list of EXACTLY length 24 corresponding to the numerical data read in each of the 24 rows, '
    'delimiting each value by a new line character and making the list vertical. '
    'This vertical list SHOULD ONLY contain 24 entries. If the response is over or under 24 in length, then you will die.'
    'On the 8th row in the image, the phrase "6-s clean up, refer to shine checklist, initials: 3rd Total:" appears.'
    'On the 16th row in the image, the phrase "6-s clean up, refer to shine checklist, initials: 1st Total:" appears.'
    'On the 24th row in the image, which is the last row, the phrase "6-s clean up, refer to shine checklist, initials: 2nd Total:" appears.'
    'For those 3 rows, only include those values, no other values should go on those rows. '
    'Sometimes there are initials, signed in capital english letters, next to "initials:".'
    'Sometimes there is a numerical value next to "Total:".'
    'Your response should only contain english words and numbers, '
    'along with the given phrases which should be placed on the 8th row, the 16th row, and the final 24th row respectively.'
    'If you move any of the numbers on the list around in a way that does not ACCURATELY depict the image.'
    'Double check response before responding.'
)

full_column_prompt = 'This is an example of what a full'



