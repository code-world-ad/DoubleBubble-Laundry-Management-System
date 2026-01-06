# DoubleBubble Laundry Management System

A full-stack Laundry Management System built with **Flask**, **SQLite**, and a modern HTML/CSS/JS frontend.  
It supports end-to-end laundry workflows for both **customers** and **owners**, including cart-based booking, saved addresses, order tracking, delivery status management, and billing with GST and PDF download.

---

## 🔍 Overview

DoubleBubble simulates a real-world laundry service portal:

- **Customers** can:
  - Sign up and log in
  - Manage a cart with multiple garments and quantities
  - Choose pickup and delivery dates
  - Save and reuse multiple addresses
  - Place orders and view complete delivery history
  - Track order statuses (Order Placed → Picked → In Process → Out for Delivery → Delivered)
  - View and download PDF bills (with GST)

- **Owners** can:
  - Log in to an owner dashboard
  - View and filter all customer orders by status
  - View pickup and delivery addresses per order
  - Update delivery status through the full lifecycle
  - Generate monthly revenue reports by month/year

The system is entirely database-driven using **SQLite** (`customer_db.sqlite`), with all CSV dependencies removed.

---

## 🧠 Tech Stack

- **Backend**
  - Python 3.x
  - Flask (routing, sessions, JSON APIs)
  - SQLite (via `sqlite3`)

- **Frontend**
  - HTML5 templates (Jinja2 via Flask)
  - CSS3 (custom, responsive layouts)
  - Vanilla JavaScript + Fetch API
  - `html2pdf.js` for client-side PDF generation

- **Other**
  - Git + GitHub for version control
  - Session-based authentication for owner and customer logins

---

## 📂 Project Structure

```text
Project files - Copy/
├─ main.py                         # Flask app entrypoint and all routes
├─ customer_db.sqlite              # Main SQLite database
│
├─ Sign_in_cust.py                 # Customer authentication & DB initialization
├─ Log_in_cust.py                  # Customer login (DB-based auth helper)
├─ Log_in_Owner.py                 # Owner login logic
│
├─ Manipulation_of_cart_edited.py  # Cart & order placement logic
├─ CustSOD.py                      # Customer "Status of Delivery" APIs
├─ OwnerSOD.py                     # Owner order & delivery management APIs
├─ monthrep.py                     # Monthly revenue reporting logic
├─ addresses.py                    # Customer saved-address management
│
├─ templates/
│  ├─ Home Page.html               # Landing page
│  ├─ General Login.html           # Combined owner & customer login/signup UI
│  ├─ cust_home_page.html          # Customer dashboard (book laundry, track orders)
│  ├─ own_home.html                # Owner dashboard (reports, delivery management)
│  ├─ Laundry Cart.html            # Cart UI, address selection, order placement
│  ├─ DeliveryStatusCust.html      # Customer orders & delivery tracking + billing
│  ├─ own_sod.html                 # Owner-side delivery status management
│  ├─ report.html                  # Monthly report UI (filters, totals)
│
└─ static/
   └─ images/                      # Backgrounds, hero images, branding assets
```

---

## 🗄️ Database Design

All data is stored in `customer_db.sqlite`. Key tables:

### `customers`

Stores registered customer accounts.

- `cust_id` (TEXT, PK)
- `username` (TEXT, UNIQUE, NOT NULL)
- `password` (TEXT, NOT NULL)
- `cust_name` (TEXT, NOT NULL)
- `mobile_no` (TEXT, 10-digit, numeric-only, NOT NULL)
- `created_at`, `updated_at` (TEXT, timestamps)

### `orders`

Stores high-level order information.

- `id` (INTEGER, PK, AUTOINCREMENT)
- `customer_id` (TEXT, FK → `customers.cust_id`)
- `customer_name` (TEXT)
- `pickup_address` (TEXT)
- `delivery_address` (TEXT)
- `order_pickup_date` (TEXT, `DD-MM-YYYY`)
- `order_delivery_date` (TEXT, `DD-MM-YYYY`)
- `bill_amount` (REAL, **includes 18% GST**)
- `bill_id` (TEXT, logical order identifier, e.g. `B001`)
- `delivery_status` (TEXT, e.g. `Order Placed`, `Order Picked`, `In Process`, `Out for Delivery`, `Delivered`, `Cancelled`)
- `cancelled_by` (TEXT, `customer` or `NULL`)
- `created_at`, `updated_at` (TEXT, timestamps)

### `cart`

Temporary per-customer cart for items before order placement.

- `id` (INTEGER, PK)
- `customer_id` (TEXT, FK)
- `item_name` (TEXT)
- `quantity` (INTEGER, `>0`)
- `unit_price` (REAL, `>=0`)
- `total_price` (REAL)
- `added_at` (TIMESTAMP)

### `order_items`

Line items for each finalized order.

- `id` (INTEGER, PK)
- `bill_id` (TEXT, FK → `orders.bill_id`)
- `item_name` (TEXT)
- `quantity` (INTEGER, `>0`)
- `unit_price` (REAL, `>=0`)
- `total_price` (REAL)

### `addresses`

Saved addresses per customer for reusable pickup/delivery.

- `id` (INTEGER, PK)
- `customer_id` (TEXT, FK)
- `address_type` (TEXT: `Home` | `Work` | `Other`)
- `full_name` (TEXT)
- `phone` (TEXT, 10-digit, numeric-only)
- `address_line1`, `address_line2` (TEXT)
- `city` (TEXT, default `Mumbai`)
- `state` (TEXT, default `Maharashtra`)
- `pincode` (TEXT, 6-digit, numeric-only)
- `landmark` (TEXT, optional)
- `is_default` (BOOLEAN)
- `created_at`, `updated_at` (TEXT)

All tables enforce appropriate `CHECK` constraints and foreign keys where applicable to maintain data integrity.

---

## 🔐 Authentication & Sessions

### Customer

- Sign up via `templates/General Login.html`
- Backend: `Sign_in_cust.py`
  - Validates inputs (name length, email format, 10-digit phone, password length)
  - Creates a new `customers` record
- Login via the same page (login mode)
  - `Sign_in_cust.customer_sign_in(request)` handles authentication
  - On success:
    - `session['customer_id']`
    - `session['customer_username']`
    - `session['customer_name']`
    - `session['logged_in'] = True`

### Owner

- Owner login option on `General Login.html`
- Backend: `Log_in_Owner.py`
  - Validates against configured owner credentials
  - On success:
    - `session['owner_logged_in'] = True`

### Sign out

- Route: `/signout`
- Clears session and redirects back to `Home Page.html`.

---

## 🧺 Core Features

### 1. Cart & Order Placement

**Frontend:** `templates/Laundry Cart.html`  
**Backend:** `Manipulation_of_cart_edited.py`, related `/api/cart/*` routes in `main.py`

- Available garments with per-item pricing
- Quantity increment/decrement with total auto-calculation
- Cart is stored in the `cart` table
- Pickup date selection (today + next 10 days)
- Saved addresses (pickup & delivery) with “Same as pickup” option
- Order placement:
  - Computes subtotal from cart items
  - Adds **18% GST** to compute `bill_amount`
  - Stores order in `orders` and items in `order_items`
  - Clears cart after successful order

Delivery date logic:
- If count of undelivered orders < 5 → next day of pickup
- Else → 2 days after pickup

---

### 2. Customer Order Tracking & Billing

**Frontend:** `templates/DeliveryStatusCust.html`  
**Backend:** `CustSOD.py`, relevant API routes in `main.py`

Features:

- Filter orders by **month** and **year**
- Cards per order showing:
  - Bill ID, dates, amount, status, items summary
- Detailed order modal:
  - Pickup/delivery addresses
  - Items breakdown
- Order stats:
  - Total orders
  - Delivered
  - Pending
  - Total amount
- Billing:
  - `/api/generate-bill/<bill_id>` returns full HTML bill
  - “View Bill” opens modal with detailed bill
  - “Print Bill” opens printer-friendly window
  - “Download Bill” uses `html2pdf.js` to produce **full-page PDF**, including all items and totals (no truncation)
- Cancellation:
  - Only available while status is **`Order Placed`**
  - Only customers can cancel
  - Owner cannot cancel; can only view `Cancelled` orders

---

### 3. Owner Order Management (Status of Delivery)

**Frontend:** `templates/own_sod.html`  
**Backend:** `OwnerSOD.py`, related routes in `main.py`

- View all orders with filters by status:
  - All Orders
  - Order Placed
  - Order Picked
  - In Process
  - Out for Delivery
  - Delivered
  - Cancelled (only those cancelled by customers)
- Each order shows:
  - Customer name
  - Bill ID
  - Pickup & delivery dates
  - Amount
  - Current status
- Click any order:
  - View detailed item list (aggregated via `GROUP_CONCAT` from `order_items`)
  - View pickup & delivery addresses
- Update status via buttons inside modal:
  - Owner can move through full delivery lifecycle
- Owner **cannot** cancel orders (business rule).

---

### 4. Monthly Reporting (Owner)

**Frontend:** `templates/report.html`  
**Backend:** `monthrep.py`, route `/monthly_report` in `main.py`

- Filter by:
  - Month (or “All Months”)
  - Year
- Results:
  - Orders in descending order of delivery date
  - Summary:
    - Total orders
    - Period displayed
    - Total revenue (sum of `bill_amount`)
- Fixes included:
  - Correct year-only filter behavior
  - Correct combination of month + year filtering

---

### 5. Saved Addresses

**Frontend:** `Laundry Cart.html` (address management modal)  
**Backend:** `addresses.py`, `/api/addresses*` routes in `main.py`

- Add / edit / delete addresses
- Client-side validation:
  - Required fields (name, phone, address line 1, city, state, pincode)
  - 10-digit phone, 6-digit pincode
- Mark one address as default
- Auto-load default address as both pickup & delivery
- Fully integrated into order placement and later display in SOD pages.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+ (3.9 recommended)
- `pip` (Python package manager)
- Git (optional but recommended)
- A modern browser (Chrome, Edge, Firefox, etc.)

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/DoubleBubble-Laundry-Management-System.git
cd DoubleBubble-Laundry-Management-System
```

### 2. Create & Activate a Virtual Environment (Recommended)

```bash
python -m venv venv
venv\Scripts\activate    # On Windows
# or
source venv/bin/activate # On macOS/Linux
```

### 3. Install Dependencies

Create a `requirements.txt` (if not already present) with at least:

```text
Flask
```

Then:

```bash
pip install -r requirements.txt
```

(If `requirements.txt` is missing, simply do `pip install Flask`.)

### 4. Run the Application

From the project root:

```bash
python main.py
```

By default, Flask will start on `http://127.0.0.1:5000` (or `http://localhost:5000`).

---

## 🌐 Key Routes

- `GET /`  
  Landing / Home page.

- `GET /login_page` (or similar, depending on `main.py` setup)  
  Renders `General Login.html`.

- `POST /signup`  
  JSON API for customer signup.

- `POST /login`  
  Handles customer or owner login, returns JSON status.

- `GET /cust_home_page`  
  Customer dashboard.

- `GET /own_home_page`  
  Owner dashboard.

- `GET /laundry_cart`  
  Customer cart UI.

- `GET /customer_delivery_status`  
  Customer delivery status page.

- `GET /own_sod.html`  
  Owner delivery status page.

- `GET /report`  
  Owner reporting page.

- `GET /monthly_report`  
  API for monthly report data.

- `GET /api/cart/items`, `POST /api/cart/add`, `POST /api/cart/place-order`, etc.  
  Cart & order placement APIs.

- `GET /api/customer/orders`, `GET /api/customer/order/<bill_id>`  
  Customer order data.

- `GET /api/generate-bill/<bill_id>`  
  Returns rendered bill HTML for printing / PDF.

- `POST /api/cancel-order/<bill_id>`  
  Customer order cancellation.

- `GET /api/addresses`, `POST /api/addresses`, `PUT /api/addresses/<id>`, `DELETE /api/addresses/<id>`  
  Saved address CRUD APIs.

- `GET /signout`  
  Clears session and redirects to home.

---

## ✅ Validation & Constraints

- **HTML-level validation**:
  - Signup: name length, email regex, 10-digit phone, min password length
  - Address forms: required fields, numeric phone/pincode patterns

- **Database-level constraints**:
  - `CHECK` on phone length and numeric content
  - `CHECK` on pincode length and numeric content
  - `CHECK` on quantity > 0; price ≥ 0
  - Foreign keys for data integrity

- **Business rules**:
  - Only customers can cancel orders
  - Cancellation allowed only when status = `Order Placed`
  - Owner cannot cancel, only update statuses

---

## 🧪 Testing & Future Enhancements

Current testing is primarily manual (via the UI and direct Flask routes).  
Suggested future improvements:

- Add automated tests (e.g., `pytest` + `Flask` test client)
- Add pagination for orders and reports
- Add role-based access control for more granular permissions
- Move hard-coded pricing and owner credentials to configuration
- Package as a Docker container for easier deployment

---

## 🏛 Architecture

The system follows a classic **3-layer web architecture**: UI (templates), API/Business Logic (Flask views + service modules), and Data (SQLite).

High-level component diagram:

```text
+-----------------------------+
|         Browser             |
|  - HTML templates           |
|  - CSS, JS, Fetch API      |
+--------------+--------------+
               |
               | HTTP (HTML & JSON)
               v
+--------------+--------------+
|        Flask App            |
|          main.py            |
|  - Routing & sessions       |
|  - REST/JSON APIs           |
|  - Renders templates        |
+--------------+--------------+
      |           |       
      |           | calls
      v           v
  +--------+   +---------------------------+
  | Auth   |   |  Business Logic Services |
  |        |   |  - Cart & Orders         |
  | Sign_in_cust.py        (Manipulation_of_cart_edited.py) |
  | Log_in_cust.py         - Customer SOD (CustSOD.py)      |
  | Log_in_Owner.py        - Owner SOD (OwnerSOD.py)        |
  +--------+   |  - Reporting (monthrep.py)                 |
               |  - Addresses (addresses.py)                |
               +---------------------------+
                              |
                              | SQL (via sqlite3)
                              v
                    +-------------------------+
                    |  SQLite Database        |
                    |  customer_db.sqlite     |
                    |                         |
                    |  - customers            |
                    |  - orders               |
                    |  - order_items          |
                    |  - cart                 |
                    |  - addresses            |
                    +-------------------------+
```

**Flow summary**
 - The **browser** loads HTML templates and uses JavaScript + Fetch API to call Flask JSON endpoints.
 - **Flask routes in `main.py`** delegate to specialized modules:
   - Authentication: `Sign_in_cust.py`, `Log_in_cust.py`, `Log_in_Owner.py`
   - Cart & orders: `Manipulation_of_cart_edited.py`
   - Customer order tracking: `CustSOD.py`
   - Owner delivery management: `OwnerSOD.py`
   - Reporting: `monthrep.py`
   - Saved addresses: `addresses.py`
 - All persistent state is stored in **SQLite** tables (`customers`, `orders`, `order_items`, `cart`, `addresses`), with business rules enforced both in code and via DB constraints.
 
 ---
 

## 🙌 Acknowledgements

- Built as part of a **Software Development Project** focusing on realistic, industry-style requirements:
  - Session-based auth
  - Data validation at multiple layers
  - Clean separation of concerns between UI, business logic, and persistence
  - Realistic order lifecycle and reporting flows


