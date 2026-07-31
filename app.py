import datetime
import os
import smtplib
import sqlite3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
import stripe
import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION & PASTEL THEME
# ==========================================
st.set_page_config(
    page_title="Nadra's Bakehouse", page_icon="🧁", layout="wide"
)

st.markdown(
    """
    <style>
    .stApp { background-color: #FFFDF9; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    .hero-banner {
        background: linear-gradient(135deg, #FFB7B2 0%, #FFDAC1 100%);
        padding: 2rem; border-radius: 15px; color: #5D4037; text-align: center; margin-bottom: 25px;
    }
    .product-card {
        background-color: #ffffff; border-radius: 12px; padding: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px;
    }
    .receipt-box {
        background-color: #FFF8F0; border: 2px dashed #FFB7B2; padding: 20px; border-radius: 10px; margin-top: 20px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Initialize Stripe API Key safely without throwing secrets errors
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", None)

# ==========================================
# 2. DATABASE MANAGEMENT (SQLite)
# ==========================================
DB_FILE = "bakehouse.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT UNIQUE,
            category TEXT,
            price REAL,
            stock_qty INTEGER,
            image_url TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            customer_phone TEXT,
            location TEXT,
            items_ordered TEXT,
            total_price REAL,
            payment_status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Standard menu setup with high-quality pastry placeholder photos
    initial_items = [
        # Individual Cupcakes
        (
            "Vanilla Cupcake",
            "Cupcake",
            2.50,
            50,
            "https://images.unsplash.com/photo-1576618148400-f54bed99fcfd?w=500",
        ),
        (
            "Chocolate Cupcake",
            "Cupcake",
            2.50,
            50,
            "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=500",
        ),
        (
            "Red Velvet Cupcake",
            "Cupcake",
            2.75,
            40,
            "https://images.unsplash.com/photo-1614707267537-b85aaf00c4b7?w=500",
        ),
        # Single Flavor Cupcake Boxes
        (
            "Vanilla Cupcakes (Box of 6)",
            "Cupcake Box",
            14.00,
            20,
            "https://images.unsplash.com/photo-1519869325930-281384150729?w=500",
        ),
        (
            "Chocolate Cupcakes (Box of 6)",
            "Cupcake Box",
            14.00,
            20,
            "https://images.unsplash.com/photo-1550617931-e17a7b70dce2?w=500",
        ),
        (
            "Red Velvet Cupcakes (Box of 6)",
            "Cupcake Box",
            15.00,
            15,
            "https://images.unsplash.com/photo-1614707267537-b85aaf00c4b7?w=500",
        ),
        (
            "Vanilla Cupcakes (Box of 12)",
            "Cupcake Box",
            26.00,
            15,
            "https://images.unsplash.com/photo-1519869325930-281384150729?w=500",
        ),
        (
            "Chocolate Cupcakes (Box of 12)",
            "Cupcake Box",
            26.00,
            15,
            "https://images.unsplash.com/photo-1550617931-e17a7b70dce2?w=500",
        ),
        (
            "Red Velvet Cupcakes (Box of 12)",
            "Cupcake Box",
            28.00,
            10,
            "https://images.unsplash.com/photo-1614707267537-b85aaf00c4b7?w=500",
        ),
        # Individual Cookies
        (
            "White Chocolate Chip Cookie",
            "Cookie",
            1.75,
            60,
            "https://images.unsplash.com/photo-1558961363-fa8fdf82db35?w=500",
        ),
        (
            "Chocolate Chip Cookie",
            "Cookie",
            1.75,
            60,
            "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?w=500",
        ),
        (
            "Triple Chocolate Chip Cookie",
            "Cookie",
            2.00,
            50,
            "https://images.unsplash.com/photo-1607920592519-bab4d7db727d?w=500",
        ),
        # Single Flavor Cookie Boxes
        (
            "White Choc Chip Cookies (Box of 6)",
            "Cookie Box",
            9.50,
            25,
            "https://images.unsplash.com/photo-1590080875515-8a3a8dc5735e?w=500",
        ),
        (
            "Chocolate Chip Cookies (Box of 6)",
            "Cookie Box",
            9.50,
            25,
            "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?w=500",
        ),
        (
            "Triple Choc Chip Cookies (Box of 6)",
            "Cookie Box",
            11.00,
            20,
            "https://images.unsplash.com/photo-1607920592519-bab4d7db727d?w=500",
        ),
        (
            "White Choc Chip Cookies (Box of 12)",
            "Cookie Box",
            18.00,
            15,
            "https://images.unsplash.com/photo-1590080875515-8a3a8dc5735e?w=500",
        ),
        (
            "Chocolate Chip Cookies (Box of 12)",
            "Cookie Box",
            18.00,
            15,
            "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?w=500",
        ),
        (
            "Triple Choc Chip Cookies (Box of 12)",
            "Cookie Box",
            20.00,
            10,
            "https://images.unsplash.com/photo-1607920592519-bab4d7db727d?w=500",
        ),
    ]

    c.execute("SELECT COUNT(*) FROM inventory")
    if c.fetchone()[0] == 0:
        c.executemany(
            "INSERT INTO inventory (item_name, category, price, stock_qty, image_url) VALUES (?, ?, ?, ?, ?)",
            initial_items,
        )

    conn.commit()
    conn.close()


init_db()


def get_inventory():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "SELECT item_name, category, price, stock_qty, image_url FROM inventory"
    )
    data = {
        row[0]: {
            "category": row[1],
            "price": row[2],
            "stock": row[3],
            "image": row[4],
        }
        for row in c.fetchall()
    }
    conn.close()
    return data


def update_stock(items_dict):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for item_name, qty in items_dict.items():
        c.execute(
            "UPDATE inventory SET stock_qty = stock_qty - ? WHERE item_name = ?",
            (qty, item_name),
        )
    conn.commit()
    conn.close()


def save_order(name, phone, location, summary_str, total, status):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO orders (customer_name, customer_phone, location, items_ordered, total_price, payment_status)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (name, phone, location, summary_str, total, status),
    )
    conn.commit()
    conn.close()


def send_email_notification(
    cust_name, cust_phone, location, summary_str, total
):
    sender_email = "nadrasbakehouse97@gmail.com"
    receiver_email = "nadrasbakehouse97@gmail.com"
    password = os.environ.get("EMAIL_PASSWORD", "")

    if not password:
        return

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = f"🧁 New Order Received from {cust_name}!"

    body = f"""
    New Order Details:
    ------------------
    Customer Name: {cust_name}
    Phone: {cust_phone}
    Meeting Location: {location}
    Items: {summary_str}
    Total Amount: £{total:.2f}
    """
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()
    except Exception:
        pass


# ==========================================
# 3. INTERFACE LAYOUT
# ==========================================
st.markdown(
    """
    <div class="hero-banner">
        <h1>🧁 NADRA'S BAKEHOUSE</h1>
        <p>Freshly Baked Sweet Treats • Manchester Meeting Point Delivery</p>
    </div>
""",
    unsafe_allow_html=True,
)

# Maker Admin Sidebar Login (Hidden from standard users)
st.sidebar.title("🔐 Maker Access")
admin_mode = st.sidebar.checkbox("Maker Admin Dashboard")

if admin_mode:
    pwd = st.sidebar.text_input("Enter Admin Password", type="password")
    if pwd == "nadra123":
        st.sidebar.success("Access Granted")
        admin_tab1, admin_tab2 = st.tabs(["📜 Sales History", "📦 Stock Levels"])

        with admin_tab1:
            st.subheader("Sales & Order History")
            conn = sqlite3.connect(DB_FILE)
            df = pd.read_sql_query(
                "SELECT * FROM orders ORDER BY id DESC", conn
            )
            conn.close()
            st.dataframe(df, use_container_width=True)

        with admin_tab2:
            st.subheader("Manage Inventory")
            inv = get_inventory()
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            for item, data in inv.items():
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.write(f"**{item}**")
                with col2:
                    new_p = st.number_input(
                        "Price (£)", value=float(data["price"]), key=f"p_{item}"
                    )
                with col3:
                    new_s = st.number_input(
                        "Stock", value=int(data["stock"]), key=f"s_{item}"
                    )
                if st.button(f"Save {item}"):
                    c.execute(
                        "UPDATE inventory SET price=?, stock_qty=? WHERE item_name=?",
                        (new_p, new_s, item),
                    )
                    conn.commit()
                    st.toast(f"Updated {item}")
            conn.close()
    else:
        st.sidebar.error("Incorrect Password")

else:
    # ------------------------------------------
    # CUSTOMER ORDERING VIEW
    # ------------------------------------------
    inventory = get_inventory()

    st.subheader("1. Your Delivery Details")
    c1, c2, c3 = st.columns(3)
    with c1:
        cust_name = st.text_input("Full Name")
    with c2:
        cust_phone = st.text_input("Phone Number")
    with c3:
        location = st.selectbox(
            "Manchester Meeting Point",
            [
                "Piccadilly Gardens",
                "St Peter's Square",
                "Manchester Victoria Station",
                "Spinningfields (Hardman Square)",
                "Northern Quarter (Stevenson Square)",
                "MediaCityUK (Piazza)",
                "Oxford Road Station",
            ],
        )

    st.write("---")
    st.subheader("2. Select Your Treats")

    cart = {}
    total_cost = 0.0
    order_items_summary = []

    # Display Menu Items in Category Tabs
    tab_cupcakes, tab_cookies, tab_mixmatch = st.tabs(
        ["🧁 Cupcakes", "🍪 Cookies", "🎨 Custom Mix & Match Boxes"]
    )

    with tab_cupcakes:
        st.write("### Individual Cupcakes & Single-Flavor Boxes")
        cupcake_items = {
            k: v
            for k, v in inventory.items()
            if v["category"] in ["Cupcake", "Cupcake Box"]
        }
        item_keys = list(cupcake_items.keys())

        for i in range(0, len(item_keys), 3):
            cols = st.columns(3)
            for idx, col in enumerate(cols):
                if i + idx < len(item_keys):
                    item_name = item_keys[i + idx]
                    details = cupcake_items[item_name]
                    with col:
                        st.markdown(
                            "<div class='product-card'>", unsafe_allow_html=True
                        )
                        st.image(
                            details["image"],
                            use_container_width=True,
                            caption=item_name,
                        )
                        st.markdown(f"**£{details['price']:.2f}**")
                        qty = st.number_input(
                            "Qty",
                            min_value=0,
                            max_value=details["stock"],
                            key=f"item_{item_name}",
                        )
                        if qty > 0:
                            cart[item_name] = qty
                            cost = qty * details["price"]
                            total_cost += cost
                            order_items_summary.append(
                                f"{qty}x {item_name} (£{cost:.2f})"
                            )
                        st.markdown("</div>", unsafe_allow_html=True)

    with tab_cookies:
        st.write("### Individual Cookies & Single-Flavor Boxes")
        cookie_items = {
            k: v
            for k, v in inventory.items()
            if v["category"] in ["Cookie", "Cookie Box"]
        }
        cookie_keys = list(cookie_items.keys())

        for i in range(0, len(cookie_keys), 3):
            cols = st.columns(3)
            for idx, col in enumerate(cols):
                if i + idx < len(cookie_keys):
                    item_name = cookie_keys[i + idx]
                    details = cookie_items[item_name]
                    with col:
                        st.markdown(
                            "<div class='product-card'>", unsafe_allow_html=True
                        )
                        st.image(
                            details["image"],
                            use_container_width=True,
                            caption=item_name,
                        )
                        st.markdown(f"**£{details['price']:.2f}**")
                        qty = st.number_input(
                            "Qty",
                            min_value=0,
                            max_value=details["stock"],
                            key=f"item_{item_name}",
                        )
                        if qty > 0:
                            cart[item_name] = qty
                            cost = qty * details["price"]
                            total_cost += cost
                            order_items_summary.append(
                                f"{qty}x {item_name} (£{cost:.2f})"
                            )
                        st.markdown("</div>", unsafe_allow_html=True)

    with tab_mixmatch:
        st.write("### Create Your Custom Assortment Box")

        col_mm1, col_mm2 = st.columns(2)

        with col_mm1:
            st.markdown(
                "#### 🧁 Mix & Match Cupcake Box (Box of 6 = £14.50 | Box of 12 = £26.00)"
            )
            cp_box_size = st.radio(
                "Cupcake Box Size", [0, 6, 12], key="cp_box_size"
            )
            if cp_box_size > 0:
                c_van = st.number_input(
                    "Vanilla Qty", min_value=0, max_value=cp_box_size, key="mm_cv"
                )
                c_choc = st.number_input(
                    "Chocolate Qty",
                    min_value=0,
                    max_value=cp_box_size,
                    key="mm_cc",
                )
                c_rv = st.number_input(
                    "Red Velvet Qty",
                    min_value=0,
                    max_value=cp_box_size,
                    key="mm_crv",
                )

                if (c_van + c_choc + c_rv) != cp_box_size:
                    st.warning(
                        f"Total selected cupcakes: {c_van + c_choc + c_rv}/{cp_box_size}"
                    )
                else:
                    box_price = 14.50 if cp_box_size == 6 else 26.00
                    total_cost += box_price
                    order_items_summary.append(
                        f"Custom Cupcake Box of {cp_box_size} ({c_van} Vanilla, {c_choc} Chocolate, {c_rv} Red Velvet) - £{box_price:.2f}"
                    )

        with col_mm2:
            st.markdown(
                "#### 🍪 Mix & Match Cookie Box (Box of 6 = £10.00 | Box of 12 = £18.00)"
            )
            ck_box_size = st.radio(
                "Cookie Box Size", [0, 6, 12], key="ck_box_size"
            )
            if ck_box_size > 0:
                ck_w = st.number_input(
                    "White Choc Chip Qty",
                    min_value=0,
                    max_value=ck_box_size,
                    key="mm_cw",
                )
                ck_c = st.number_input(
                    "Chocolate Chip Qty",
                    min_value=0,
                    max_value=ck_box_size,
                    key="mm_cck",
                )
                ck_t = st.number_input(
                    "Triple Choc Chip Qty",
                    min_value=0,
                    max_value=ck_box_size,
                    key="mm_ct",
                )

                if (ck_w + ck_c + ck_t) != ck_box_size:
                    st.warning(
                        f"Total selected cookies: {ck_w + ck_c + ck_t}/{ck_box_size}"
                    )
                else:
                    box_price = 10.00 if ck_box_size == 6 else 18.00
                    total_cost += box_price
                    order_items_summary.append(
                        f"Custom Cookie Box of {ck_box_size} ({ck_w} White Choc, {ck_c} Choc Chip, {ck_t} Triple Choc) - £{box_price:.2f}"
                    )

    st.write("---")
    st.markdown(f"### 💰 Total Amount: **£{total_cost:.2f}**")

    if st.button("Complete Order & Pay 💳"):
        if not cust_name.strip() or not cust_phone.strip():
            st.error("Please fill in your name and phone number.")
        elif total_cost == 0:
            st.warning("Your cart is empty! Please select some baked goods.")
        else:
            summary_str = "; ".join(order_items_summary)
            save_order(
                cust_name,
                cust_phone,
                location,
                summary_str,
                total_cost,
                "Paid (Simulated)",
            )
            update_stock(cart)
            send_email_notification(
                cust_name, cust_phone, location, summary_str, total_cost
            )

            st.balloons()
            st.success("🎉 Payment Received! Order recorded.")

            # Printable Receipt Output
            st.markdown("<div class='receipt-box'>", unsafe_allow_html=True)
            st.markdown("### 🧾 NADRA'S BAKEHOUSE RECEIPT")
            st.write(
                f"**Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            st.write(f"**Customer Name:** {cust_name}")
            st.write(f"**Phone:** {cust_phone}")
            st.write(f"**Meeting Location:** {location}")
            st.write("---")
            st.write(f"**Items Ordered:** {summary_str}")
            st.write(f"**Total Paid:** £{total_cost:.2f}")
            st.markdown("</div>", unsafe_allow_html=True)