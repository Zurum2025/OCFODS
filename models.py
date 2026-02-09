from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    role = db.Column(db.String(20), nullable=False)  
    # "customer", "vendor", "admin"

    name = db.Column(db.String(120))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))

    # Vendor-only fields
    business_name = db.Column(db.String(150))
    logo = db.Column(db.String(255))
    is_active= db.Column(db.Boolean, default = True)

class Food(db.Model):
    __tablename__ = "foods"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    availability = db.Column(db.Boolean, default=True)

    vendor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("food_categories.id"), nullable=False)

    vendor = db.relationship("User", backref="foods")
    category = db.relationship("FoodCategory", backref="foods")
    is_active = db.Column(db.Boolean, default = True)

class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, default=db.func.now())
    status = db.Column(db.String(30), default="pending")
    total_amount = db.Column(db.Float, default=0)

    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    customer = db.relationship("User", foreign_keys=[customer_id])
    vendor = db.relationship("User", foreign_keys=[vendor_id])

class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)

    quantity = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey("foods.id"), nullable=False)

    order = db.relationship("Order", backref="items")
    food = db.relationship("Food")



class FoodCategory(db.Model):
    __tablename__ = "food_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)



class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    payment_method = db.Column(db.String(50))
    payment_status = db.Column(db.String(30), default="pending")

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), unique=True)

    order = db.relationship("Order", backref="payment")



class Rating(db.Model):
    __tablename__ = "ratings"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)

    rating = db.Column(db.Integer, nullable=False)  # 1–5
    comment = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "order_id", name="one_rating_per_order"),
    )
