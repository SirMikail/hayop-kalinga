import streamlit as st
import pandas as pd
import plotly.express as px
from collections import Counter

# Sample DataFrame
df = pd.read_excel('openai_dataset.xlsx')
df['diseases_lowercase'] = df['diseases_lowercase'].apply(eval)
df['surgeries'] = df['surgeries'].apply(eval)
df['checkups'] = df['checkups'].apply(eval)
df['vaccinations'] = df['vaccinations'].apply(eval)
df['tests_done'] = df['tests_done'].apply(eval)

# Ensure 'age' column is in numeric format, coerce errors to NaN
df['age'] = pd.to_numeric(df['age'], errors='coerce')

# Create dropdown for selecting the type of filter (diseases, surgeries, checkups, vaccinations, tests_done)
filter_type = st.sidebar.selectbox(
    'Select Filter Type',
    options=['diseases_lowercase', 'surgeries', 'checkups', 'vaccinations', 'tests_done'],
    index=0
)

# Create dropdown for selecting the doctor name
doctor_names = df['doctor_name'].dropna().unique().tolist()
selected_doctors = st.sidebar.multiselect(
    'Select Doctor(s)',
    options=doctor_names,
    default=doctor_names
)

# Filter the DataFrame based on the selected filter type and only show entries where the selected list column is not empty
if filter_type == 'diseases_lowercase':
    df = df[df['diseases_lowercase'].apply(lambda x: len(x) > 0)]
elif filter_type == 'surgeries':
    df = df[df['surgeries'].apply(lambda x: len(x) > 0)]
elif filter_type == 'checkups':
    df = df[df['checkups'].apply(lambda x: len(x) > 0)]
elif filter_type == 'vaccinations':
    df = df[df['vaccinations'].apply(lambda x: len(x) > 0)]
elif filter_type == 'tests_done':
    df = df[df['tests_done'].apply(lambda x: len(x) > 0)]

# Filter the DataFrame based on selected doctors
if selected_doctors:
    df = df[df['doctor_name'].isin(selected_doctors)]
    # df.to_excel('elysh_surgery.xlsx')

# Count occurrences for each family
family_counts = df['family'].value_counts()
sorted_families = family_counts.index.tolist()

# Create checkboxes for selecting families
selected_families = st.sidebar.multiselect(
    'Select Families',
    options=sorted_families,
    default=sorted_families
)

df = df
# Count occurrences for each breed within selected families
if selected_families:
    df = df[df['family'].isin(selected_families)]
    breed_counts = df['breed'].value_counts()
    sorted_breeds = breed_counts.index.tolist()
else:
    sorted_breeds = []

# Create checkboxes for selecting breeds
selected_breeds = st.sidebar.multiselect(
    'Select Breeds',
    options=sorted_breeds,
    default=sorted_breeds
)

# Count occurrences for each sex
sex_counts = df['gender'].value_counts()
sorted_sex = sex_counts.index.tolist()

# Create checkboxes for selecting sex
selected_sex = st.sidebar.multiselect(
    'Select Sex',
    options=sorted_sex,
    default=sorted_sex
)

# Filter the DataFrame based on selected families, breeds, and sex
if selected_families:
    df = df[df['family'].isin(selected_families)]

if selected_breeds:
    df = df[df['breed'].isin(selected_breeds)]

if selected_sex:
    df = df[df['gender'].isin(selected_sex)]

# Add a keyword filter for diseases/surgeries/checkups/vaccinations/tests_done
search_keywords = st.sidebar.text_input("Search Keywords (comma-separated)").split(',')

# Clean up and filter based on multiple keywords
search_keywords = [keyword.strip().lower() for keyword in search_keywords if keyword.strip()]

if search_keywords:
    df = df[df[filter_type].apply(lambda items: any(keyword in item.lower() for keyword in search_keywords for item in items))]

# Group data by 'year' and 'month'
grouped_data = df.groupby(['year', 'month']).size().reset_index(name='count')

# Ensure all months are included
grouped_data['date'] = pd.to_datetime(grouped_data[['year', 'month']].assign(day=1))
grouped_data = grouped_data.set_index('date').asfreq('MS', fill_value=0).reset_index()

# Plotting with Plotly
plot_type = st.sidebar.radio("Choose Plot Type", ('Line Plot', 'Histogram', 'Age Plot'))

if plot_type in ['Line Plot', 'Histogram']:
    if plot_type == 'Line Plot':
        fig = px.line(grouped_data, x='date', y='count', markers=True,
                      labels={'date': 'Year-Month', 'count': 'Count'},
                      title=f'Count Over Time')
    elif plot_type == 'Histogram':
        fig = px.bar(grouped_data, x='date', y='count',
                     labels={'date': 'Year-Month', 'count': 'Count'},
                     title=f'Count Over Time')

    # Customize layout to make the plot scrollable
    fig.update_layout(
        xaxis=dict(
            rangeslider=dict(visible=True),
            type="date",
            tickformat="%Y-%m",
            showgrid=True,
        ),
        yaxis=dict(
            tickformat="d"
        ),
        height=600,
        width=1000
    )

    st.plotly_chart(fig)

elif plot_type == 'Age Plot':
    # Group data by age
    age_data = df.groupby('age').size().reset_index(name='count')

    # Plotting age distribution
    fig = px.bar(age_data, x='age', y='count',
                 labels={'age': 'Age', 'count': 'Count'},
                 title='Age Distribution')

    # Customize layout
    fig.update_layout(
        xaxis=dict(
            tickformat="d",
            showgrid=True,
        ),
        yaxis=dict(
            tickformat="d"
        ),
        height=600,
        width=1000
    )

    st.plotly_chart(fig)

# Count unique diseases/surgeries/checkups/vaccinations/tests_done and their occurrences
all_items = [item for sublist in df[filter_type] for item in sublist]
item_counts = df[filter_type].explode().value_counts()

# Convert the counts into a DataFrame
item_counts_df = pd.DataFrame(list(item_counts.items()), columns=['Item', 'Count']).sort_values(by='Count', ascending=False)

# Display the item counts table
st.write(f"### {filter_type.capitalize()} Counts")
st.dataframe(item_counts_df, height=300)

# Display counts for selected options in the sidebar
with st.sidebar:
    st.write("### Selected Families and Their Counts")
    family_counts_df = pd.DataFrame(list(family_counts.items()), columns=['Family', 'Count'])
    st.dataframe(family_counts_df, height=300)

    if selected_families:
        st.write("### Selected Breeds and Their Counts")
        df = df[df['family'].isin(selected_families)]
        breed_counts = df['breed'].value_counts()
        breed_counts_df = pd.DataFrame(list(breed_counts.items()), columns=['Breed', 'Count'])
        st.dataframe(breed_counts_df, height=300)

    st.write("### Selected Sexes and Their Counts")
    sex_counts_df = pd.DataFrame(list(sex_counts.items()), columns=['Sex', 'Count'])
    st.dataframe(sex_counts_df, height=300)

    st.write("### Selected Doctor(s) and Their Counts")
    doctor_counts = df['doctor_name'].value_counts()
    doctor_counts_df = pd.DataFrame(list(doctor_counts.items()), columns=['Doctor', 'Count'])
    st.dataframe(doctor_counts_df, height=300)
