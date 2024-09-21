import streamlit as st
import pandas as pd
import plotly.express as px

# Sample DataFrame loading
df = pd.read_excel('openai_dataset.xlsx')
df['diseases_lowercase'] = df['diseases_lowercase'].apply(eval)
df['surgeries'] = df['surgeries'].apply(eval)
df['checkups'] = df['checkups'].apply(eval)
df['vaccinations'] = df['vaccinations'].apply(eval)
df['tests_done'] = df['tests_done'].apply(eval)

# Ensure 'age' column is in numeric format
df['age'] = pd.to_numeric(df['age'], errors='coerce')

# Cache the results for performance
@st.cache_data
def load_data():
    return df

df = load_data()

# Filters for doctor, family, breed, sex
filter_type = st.sidebar.selectbox(
    'Select Filter Type',
    options=['diseases_lowercase', 'surgeries', 'checkups', 'vaccinations', 'tests_done'],
    index=0
)

doctor_names = df['doctor_name'].dropna().unique().tolist()
selected_doctors = st.sidebar.multiselect('Select Doctor(s)', options=doctor_names, default=doctor_names)

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

# Filter by selected doctors
if selected_doctors:
    df = df[df['doctor_name'].isin(selected_doctors)]

# Family filter
family_counts = df['family'].value_counts()
sorted_families = family_counts.index.tolist()
selected_families = st.sidebar.multiselect('Select Families', options=sorted_families, default=sorted_families)

# Filter by family and breeds
if selected_families:
    df = df[df['family'].isin(selected_families)]
breed_counts = df['breed'].value_counts()
sorted_breeds = breed_counts.index.tolist()
selected_breeds = st.sidebar.multiselect('Select Breeds', options=sorted_breeds, default=sorted_breeds)

# Filter by sex
sex_counts = df['gender'].value_counts()
sorted_sex = sex_counts.index.tolist()
selected_sex = st.sidebar.multiselect('Select Sex', options=sorted_sex, default=sorted_sex)

if selected_breeds:
    df = df[df['breed'].isin(selected_breeds)]
if selected_sex:
    df = df[df['gender'].isin(selected_sex)]

# Keyword filter for diseases/surgeries/checkups/vaccinations/tests_done
search_keywords = st.sidebar.text_input("Search Keywords (comma-separated)").split(',')
search_keywords = [keyword.strip().lower() for keyword in search_keywords if keyword.strip()]

if search_keywords:
    df = df[df[filter_type].apply(lambda items: any(keyword in item.lower() for keyword in search_keywords for item in items))]

# Add frequency selection
freq_options = {'Month': 'M', 'Year': 'Y'}
freq_choice = st.sidebar.selectbox("Choose Frequency", options=list(freq_options.keys()), index=0)
freq = freq_options[freq_choice]

# Group by date with selected frequency
df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
grouped_data = df.groupby(pd.Grouper(key='date', freq=freq)).size().reset_index(name='count')

# Add total row
total_count = grouped_data['count'].sum()
total_row = pd.DataFrame({'date': ['Total'], 'count': [total_count]})
grouped_data_with_total = pd.concat([grouped_data, total_row], ignore_index=True)

# Plot
plot_type = st.sidebar.radio("Choose Plot Type", ('Line Plot', 'Histogram', 'Age Plot'))

if plot_type == 'Line Plot':
    fig = px.line(grouped_data, x='date', y='count', markers=True, title='Count Over Time')
elif plot_type == 'Histogram':
    fig = px.bar(grouped_data, x='date', y='count', title='Count Over Time')
elif plot_type == 'Age Plot':
    age_data = df.groupby('age').size().reset_index(name='count')
    fig = px.bar(age_data, x='age', y='count', title='Age Distribution')

# Display the table of counts with total
st.write("### Date and Count Table")
st.dataframe(grouped_data_with_total)

# Display the plot
st.plotly_chart(fig)

# Display distinct keyword counts
keyword_counts = df[filter_type].explode().value_counts()
keyword_counts_df = pd.DataFrame(keyword_counts).reset_index()
keyword_counts_df.columns = ['Keyword', 'Count']
st.write(f"### Distinct {filter_type.capitalize()} Keyword Counts")
st.dataframe(keyword_counts_df)

# Additional summary tables
st.sidebar.write("### Selected Families and Their Counts")
family_counts_df = pd.DataFrame(list(family_counts.items()), columns=['Family', 'Count'])
st.sidebar.dataframe(family_counts_df)

if selected_families:
    breed_counts_df = pd.DataFrame(list(breed_counts.items()), columns=['Breed', 'Count'])
    st.sidebar.write("### Selected Breeds and Their Counts")
    st.sidebar.dataframe(breed_counts_df)

sex_counts_df = pd.DataFrame(list(sex_counts.items()), columns=['Sex', 'Count'])
st.sidebar.write("### Selected Sexes and Their Counts")
st.sidebar.dataframe(sex_counts_df)

doctor_counts = df['doctor_name'].value_counts()
doctor_counts_df = pd.DataFrame(list(doctor_counts.items()), columns=['Doctor', 'Count'])
st.sidebar.write("### Selected Doctor(s) and Their Counts")
st.sidebar.dataframe(doctor_counts_df)
