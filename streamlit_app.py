import copy

import streamlit as st
from shillelagh.backends.apsw.db import connect

# chart_data = pd.DataFrame({"hi": {"a": 1, "b": 2, "c": 3}})
# # chart_data = [[1, 2, 3], [4, 5, 6]]
# chart_data.set_axis(["x", "y", "z"], axis=0)
# st.bar_chart({"hi": {"abc"[i]: i for i in range(3)}})


# _ROWS = list(cursor.execute(query))

_ROWS = []

COUNTER = 0

cost_range = (0, 0)

sheet_url = st.secrets["public_gsheets_url"]

query = f'SELECT * FROM "{sheet_url}"'

conn = connect(":memory:")
cursor = conn.cursor()

_ROWS = list(cursor.execute(query))
_ROWS = sorted(_ROWS, key=lambda x: x[5])
_HIGH = _ROWS[-2][5] + 1

_COPY = copy.copy(_ROWS)
cost_range = st.slider(
    label="Cost Range (Yearly)",
    min_value=0.0,
    max_value=_HIGH,
    value=(0.0, _HIGH),
)

for row in _COPY:
    if row[0].lower() in ["total", "test"]:
        _ROWS.remove(row)

    elif not cost_range[0] < row[5] < cost_range[1]:
        _ROWS.remove(row)

cost_type = st.radio(
    label="Cost Denomination",
    options=[3, 4, 5],
    format_func=lambda x: [0, 0, 0, "Daily", "Monthly", "Yearly"][x],
)


st.bar_chart({"cost (in dollars)": {row[0]: row[int(cost_type)] for row in _ROWS}})
