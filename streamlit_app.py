import streamlit as st
from shillelagh.backends.apsw.db import connect

# chart_data = pd.DataFrame({"hi": {"a": 1, "b": 2, "c": 3}})
# # chart_data = [[1, 2, 3], [4, 5, 6]]
# chart_data.set_axis(["x", "y", "z"], axis=0)
# st.bar_chart({"hi": {"abc"[i]: i for i in range(3)}})

sheet_url = st.secrets["public_gsheets_url"]

conn = connect(":memory:")
cursor = conn.cursor()

query = f'SELECT * FROM "{sheet_url}"'
rows = list(cursor.execute(query))

for row in rows:
    if row[0].lower() in ["total", "test"]:
        rows.remove(row)

"""Cost of electrical appliances."""

cost_type = st.radio(
    label="Cost Frequency",
    options=[3, 4, 5],
    format_func=lambda x: [0, 0, 0, "Daily", "Weekly", "Yearly"][x],
)

st.bar_chart({"cost (in dollars)": {row[0]: row[int(cost_type)] for row in rows}})
