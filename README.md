## 🛒 Smart Grocery Cart

A shopping cart app with budgets and item priorities. Set a total budget (and optional per-category budgets), then add items. If something doesn't fit, the app auto-removes lower-priority items to make room — or asks you what to remove if it can't decide.

**Stack:** C (cart logic) → Python `ctypes` wrapper → Streamlit UI

### 🚀 Run it

```bash
gcc -shared -fPIC -o libcart.so cart.c   # Windows: cart.dll instead
pip install streamlit pandas matplotlib
streamlit run app.py
```