# SEAMLESS

## A Location-Aware Multi-Vendor Food Ordering and Delivery Platform

Seamless is a full-stack web application that connects students with food vendors within a campus environment. The platform allows students to browse vendor menus, place orders, make online payments, download receipts, rate vendors, and track food delivery logistics. Vendors can manage menus, accept orders, calculate delivery charges automatically, view business analytics, and manage their food business through a dedicated dashboard.

The system combines e-commerce, geolocation services, digital payments, analytics, and delivery management into a single platform.

---

# Table of Contents

1. Project Overview
2. Features
3. System Architecture
4. Technology Stack
5. Project Structure
6. User Roles
7. Database Design
8. Order Workflow
9. Delivery & Geolocation Workflow
10. Payment Workflow
11. Analytics Dashboard
12. Vendor Dashboard
13. Receipt Generation
14. Installation Guide
15. Environment Variables
16. Database Migration
17. Running the Application
18. Screenshots & Diagrams
19. Future Enhancements
20. License

---

# Project Overview

CampusEats was developed to solve the challenge of food ordering within campus environments where students need a convenient way to order meals from nearby vendors.

Unlike traditional restaurant websites, CampusEats supports:

* Multiple vendors
* Dynamic menu management
* Online payments
* Delivery fee calculation
* Customer ratings
* Vendor analytics
* Interactive maps
* Delivery route visualization

The platform is designed using Flask and follows a modular architecture that separates presentation, business logic, and data persistence layers.

---

# Features

## Student Features

### Authentication

* Student Registration
* Student Login
* Secure Session Management

### Food Ordering

* Browse Vendors
* Browse Menus
* Filter by Category
* Select Multiple Food Items
* Review Order Before Payment

### Location-Aware Ordering

* Browser Geolocation Access
* Automatic Distance Calculation
* Dynamic Transportation Fee Calculation

### Payment

* Paystack Integration
* Secure Payment Verification
* Transaction Reference Storage

### Receipts

* PDF Receipt Generation
* Receipt Download

### Ratings

* Vendor Rating System
* Star-Based Feedback
* Order-Based Rating Validation

### Order History

* View Previous Orders
* Download Receipts

---

## Vendor Features

### Vendor Registration

* Business Registration
* Logo Upload
* Business Information Management

### Menu Management

* Add Food Items
* Edit Food Prices
* Toggle Availability
* Categorize Food Items

### Location Management

* Store Vendor Coordinates
* Save Business Address
* Configure Delivery Rate Per Kilometer

### Order Management

* Receive Incoming Orders
* Accept Orders
* Mark Orders as Ready
* Mark Orders as Delivered

### Analytics

* Order Trends
* Revenue Trends
* Popular Foods
* Vendor Performance Metrics

---

# System Architecture

The application follows a three-tier architecture.

---

## Presentation Layer

Responsible for:

* User Interface
* User Interaction
* Visual Analytics

Technologies:

* HTML5
* CSS3
* JavaScript
* Jinja2 Templates
* Chart.js
* Leaflet.js

---

## Application Layer

Responsible for:

* Authentication
* Authorization
* Business Logic
* Payment Verification
* Delivery Calculations
* Analytics Processing

Technology:

* Flask

---

## Data Layer

Responsible for:

* Data Storage
* Relationships
* Queries

Technologies:

* SQLite
* SQLAlchemy ORM

---

# Architecture Diagram

**Insert Architecture Diagram Here**

Suggested Diagram:

[ Client Browser ]
|
v
[ Flask Application ]
|
v
[ SQLAlchemy ORM ]
|
v
[ SQLite Database ]

Additional Components:

* Paystack API
* OpenStreetMap
* Leaflet.js
* Geopy

---

# 🛠 Technology Stack

## Backend

| Technology    | Purpose               |
| ------------- | --------------------- |
| Flask         | Web Framework         |
| Flask-Login   | Authentication        |
| SQLAlchemy    | ORM                   |
| Flask-Migrate | Database Migration    |
| ReportLab     | PDF Receipts          |
| Geopy         | Distance Calculations |
| Paystack      | Payment Processing    |

---

## Frontend

| Technology    | Purpose       |
| ------------- | ------------- |
| HTML5         | Structure     |
| CSS3          | Styling       |
| JavaScript    | Interactivity |
| Chart.js      | Analytics     |
| Leaflet.js    | Maps          |
| OpenStreetMap | Map Tiles     |

---

# Project Structure

Insert actual folder structure here.

Example:

project/

├── app.py

├── models.py

├── static/

│   ├── css/

│   ├── images/

│   └── receipts/

├── templates/

│   ├── student/

│   ├── vendor/

│   ├── admin/

│   └── base.html

├── migrations/

├── requirements.txt

└── README.md

---

# User Roles

## Student

Can:

* Place Orders
* Pay Online
* Download Receipts
* Rate Vendors

---

## Vendor

Can:

* Manage Menu
* Receive Orders
* Configure Delivery Settings
* View Analytics

---

## Administrator

Can:

* Manage Users
* Manage Vendors
* Monitor Platform Activities

---

# Database Design

## Entity Relationship Diagram

**Insert ER Diagram Here**

Suggested Entities:

User

FoodCategory

Food

Order

OrderItem

Payment

Rating

---

## User Table

Stores:

* Students
* Vendors
* Administrators

Key Fields:

* id
* role
* name
* email
* password
* phone
* business_name
* logo
* latitude
* longitude
* address
* delivery_fee_per_km

---

## Food Table

Stores food menu items.

Fields:

* id
* name
* price
* availability
* vendor_id
* category_id

---

## Order Table

Stores customer transactions.

Fields:

* id
* order_date
* status
* total_amount
* receipt_file
* transaction_ref
* customer_latitude
* customer_longitude
* delivery_distance_km
* transportation_fee

---

## OrderItem Table

Stores order contents.

Fields:

* order_id
* food_id
* quantity
* subtotal

---

## Payment Table

Stores payment records.

Fields:

* payment_method
* payment_status

---

## Rating Table

Stores customer reviews.

Fields:

* user_id
* vendor_id
* order_id
* rating
* comment

---

# Order Workflow

## Step 1

Student selects food items.

---

## Step 2

Browser requests location access.

---

## Step 3

Location coordinates are captured.

---

## Step 4

Distance is calculated.

Using:

Geopy Geodesic

---

## Step 5

Transportation fee is calculated.

Formula:

Transportation Fee =
Distance × Vendor Rate

Example:

5 km × ₦200

= ₦1000

---

## Step 6

Student reviews order.

Displays:

* Food Cost
* Transportation Fee
* Total Cost

---

## Step 7

Payment is completed through Paystack.

---

## Step 8

Payment verification occurs.

---

## Step 9

Order is created.

Status:

pending

---

## Step 10

Order appears on Vendor Dashboard.

---

# Delivery Workflow

Current Status Lifecycle:

pending

↓

accepted

↓

ready

↓

delivered

Definitions:

Pending:
Customer paid successfully.

Accepted:
Vendor accepted order.

Ready:
Food prepared and ready for pickup/delivery.

Delivered:
Order completed.

---

# Location System

CampusEats uses browser geolocation.

Vendor Location:

* Saved in Settings
* Used for delivery calculations

Customer Location:

* Captured during ordering
* Stored with order

Distance Calculation:

Geopy Geodesic

Future Upgrade:

OpenRouteService Routing

---

# Payment Workflow

Provider:

Paystack

Process:

Student

↓

Payment Page

↓

Paystack Checkout

↓

Verification Callback

↓

Order Creation

↓

Receipt Generation

---

# Receipt Generation

Generated Automatically After Payment

Generated Using:

ReportLab

Contents:

* Order ID
* Customer Name
* Vendor Name
* Food Items
* Transportation Fee
* Total Amount
* Transaction Reference

---

# Analytics Dashboard

Current Analytics:

## Food Popularity

Bar Chart

Categories:

* General
* Main
* Toppings
* Drinks

---

## Vendor Popularity

Doughnut Chart

Modes:

* By Orders
* By Ratings

---

## Revenue Trends

Line Chart

Modes:

* Daily
* Weekly
* Monthly
* Yearly

---

# Screenshots

Insert screenshots of:

### Landing Page

[Insert Screenshot]

### Student Dashboard

[Insert Screenshot]

### Vendor Dashboard

[Insert Screenshot]

### Menu Page

[Insert Screenshot]

### Order Review Page

[Insert Screenshot]

### Payment Page

[Insert Screenshot]

### Analytics Dashboard

[Insert Screenshot]

### Vendor Order Details Map

[Insert Screenshot]

---

# Installation Guide

Clone Repository:

git clone <repository-url>

cd campuseats

---

Create Virtual Environment:

python -m venv venv

---

Activate Environment:

Windows:

venv\Scripts\activate

Linux/Mac:

source venv/bin/activate

---

Install Dependencies:

pip install -r requirements.txt

---

# Environment Variables

Create a .env file.

Required Variables:

SECRET_KEY=

PAYSTACK_SECRET_KEY=

PAYSTACK_PUBLIC_KEY=

DATABASE_URL=

---

# Database Migration

Initialize:

flask db init

Create Migration:

flask db migrate -m "initial migration"

Apply Migration:

flask db upgrade

---

# Running the Application

python app.py

Application:

http://127.0.0.1:5000

---

# Future Enhancements

## Real-Time Notifications

Flask-SocketIO

---

## Live Delivery Tracking

Customer Tracking Dashboard

---

## OpenRouteService Integration

Route Visualization

Turn-by-Turn Navigation

---

## AI Recommendation Engine

Personalized Food Suggestions

---

## Heatmap Analytics

Vendor Delivery Zones

---

## Mobile Application

Flutter-Based Client

---

# Contributing

Pull requests are welcome.

For major changes, open an issue first to discuss proposed modifications.

---

# License

This project is provided for educational and research purposes.

---

# Author

Developed as a full-stack location-aware food ordering platform using Flask, SQLAlchemy, Paystack, Geopy, Leaflet.js, and modern web technologies.

CampusEats demonstrates practical implementation of:

* Authentication Systems
* Payment Processing
* Geospatial Computing
* Database Design
* Business Analytics
* E-Commerce Workflows
* Delivery Logistics
* Full-Stack Web Development
