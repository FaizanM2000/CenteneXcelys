import streamlit as st
import pandas as pd
import os 


# The main script for processing
def process_data(file):
    data = pd.read_excel(file)
    # Group by PPKGT_TEMPLATE_ID
    grouped = data.groupby('PPKGT_TEMPLATE_ID')
    print("length after ID grouping", len(grouped))
    specified_price_rules = ['DMETR', 'FFSTR', 'MCRIL']

    # Function to check if any price rule in a group is outside of the specified rules
    def has_invalid_rule(group):
        unique_rules = group['PRICE_RULE_1'].unique()
        return any(rule not in specified_price_rules for rule in unique_rules)

    # Find valid PPKGT_TEMPLATE_IDs (Groups without invalid rules and with more than one item)
    valid_template_ids = [name for name, group in grouped if not has_invalid_rule(group) and len(group) >= 1]
    print("length after removing invalid price rules", len(valid_template_ids))

    # Filter out the valid groups
    final_filtered_data = data[data['PPKGT_TEMPLATE_ID'].isin(valid_template_ids)]

    # Print the sizes of the final groups
    group_size_counts = final_filtered_data.groupby('PPKGT_TEMPLATE_ID').size().value_counts()
    print()
    filtered_group_size_counts = group_size_counts[group_size_counts > 1]
    print(filtered_group_size_counts)
    print(len(group_size_counts))
    cols_to_compare = [
        'PRICE_SCHEDULE', 'SCHED_PCT_ALLOWED', 'PCT_ALLOWED', 
        'PCT_OF_BILLED', 'PRICE_RULE_1', 'DETERMINANT', 'DETERMINANT_TABLE',
        'PCT_WITHHOLD'
    ]

    duplicates = []

    # Get group sizes that appear more than once
    valid_group_sizes = filtered_group_size_counts.index.tolist()

    for size in valid_group_sizes:
        # Get all groups of the current size
        groups_of_size = final_filtered_data.groupby('PPKGT_TEMPLATE_ID').filter(lambda x: len(x) == size)
        
        unique_ppkgts = groups_of_size['PPKGT_TEMPLATE_ID'].unique()

        for i in range(len(unique_ppkgts)):
            for j in range(i+1, len(unique_ppkgts)):
                group1 = groups_of_size[groups_of_size['PPKGT_TEMPLATE_ID'] == unique_ppkgts[i]]
                group2 = groups_of_size[groups_of_size['PPKGT_TEMPLATE_ID'] == unique_ppkgts[j]]
                
                matched = True
                for col in cols_to_compare:
                    if col == 'PRICE_RULE_1':
                        valid_price_rules = ['DMETR', 'FFSTR', 'MCRIL']
                        if not (group1[col].iloc[0] in valid_price_rules and group2[col].iloc[0] in valid_price_rules):
                            print(f"Invalid price rule compared: {group1[col].iloc[0]} and {group2[col].iloc[0]}")
                    
                    if not group1[col].reset_index(drop=True).equals(group2[col].reset_index(drop=True)):
                        matched = False
                        break
                
                if matched:
                    # Further check for 'DET_VALUE_FROM' and 'DET_VALUE_TO' columns
                    
                    if  sorted(group1['DET_VALUE_FROM'].astype(str).unique()) == sorted(group2['DET_VALUE_FROM'].astype(str).unique()) and \
                        sorted(group1['DET_VALUE_TO'].astype(str).unique()) == sorted(group2['DET_VALUE_TO'].astype(str).unique()):
                    
                        duplicates.append((unique_ppkgts[i], unique_ppkgts[j]))
                    
    # Print duplicates
    for dup in duplicates:
        print(f"Duplicates found: PPKGT_TEMPLATE_ID {dup[0]} and {dup[1]}")
    print(len(duplicates))

    return duplicates

def main():
    st.title("Duplicate PPKGT_TEMPLATE_ID Finder")
    
    uploaded_file = st.file_uploader("Choose a file", type=["xlsx"])
    
    if uploaded_file is not None:
        with st.spinner("Processing data..."):
            results = process_data(uploaded_file)
        
        if results:
            st.subheader("Duplicates found:")
            st.write(pd.DataFrame(results, columns=["PPKGT_TEMPLATE_ID 1", "PPKGT_TEMPLATE_ID 2"]))
            
            csv = pd.DataFrame(results).to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="duplicates.csv">Download CSV File</a>'
            st.markdown(href, unsafe_allow_html=True)

            # Delete the Excel file after processing and providing download link
            try:
                os.remove(uploaded_file.name)
            except Exception as e:
                st.warning(f"An error occurred when deleting the file: {e}")
                

        else:
            st.write("No duplicates found!")

if __name__ == "__main__":
    import base64
    main()







