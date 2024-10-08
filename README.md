Medium Article available here

https://medium.com/@haselebe/building-a-database-for-an-e-voucher-system-a-data-analysts-perspective-2acec0aa2af9



Michael Aselebe
Building a Database for an E-Voucher System: A Data Analyst’s Perspective


As a data analyst and database administrator (DBA), I had the opportunity to collaborate closely with software developers on an innovative project — the E-Voucher System. This web-based application enables sellers to manage vouchers and track sales, while administrators can monitor transactions across multiple booths, all via a user-friendly platform.

My role in this project was crucial to ensure that the system’s data architecture was well-defined, secure, and highly functional, allowing for seamless integration with the application’s key features, such as QR code generation and email notifications.

In this article, I’ll walk through the steps and considerations that went into creating a reliable database, as well as the collaboration process that made this project a success.

Project Collaboration: Aligning Objectives with Software Developers

Working on this project as a data analyst meant I was responsible for designing the database structure and ensuring its compatibility with the application’s requirements. The software development team, working on the back-end and front-end components, relied on a robust and scalable database to support the key features of the system.


The collaboration between the data team and software developers was essential. The developers needed a fast, secure database to store and retrieve voucher information, booth details, and sales records. Meanwhile, I ensured that the database could handle concurrent operations efficiently and that the necessary data relationships were maintained for accurate reporting.

Key Collaboration Steps:

Requirements Gathering: We first discussed the application’s workflow, identifying the key data entities (vouchers, booths, sales) that the database would need to support. The developers emphasized the need for quick data retrieval for sales logging and voucher redemption in real-time, which informed decisions about indexing and query optimization.
Defining the Schema: The project relied on a Flask back-end, with SQLite as the database system. We designed a schema that would optimize query efficiency while ensuring data integrity. Three primary tables were defined: booths, vouchers, and sales. The relationships between these tables ensured proper linkage of voucher sales to the correct booths and enabled comprehensive sales tracking.

Designing the Database
The database structure was fundamental to the E-Voucher System’s operations. Here’s a breakdown of the key tables and how they were designed to support the application:

1. Booths Table
This table stored essential details about the individual booths where vouchers would be redeemed. It included fields like booth_id (the primary key) and operator (username), both indexed to ensure quick lookups for authentication during login.

CREATE TABLE booths (
    booth_id INTEGER PRIMARY KEY AUTOINCREMENT,
    booth_name TEXT NOT NULL,
    location TEXT NOT NULL,
    operator TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);
2. Vouchers Table
Each voucher generated had to be uniquely identifiable, with an association to the buyer’s email and its redemption status. We also needed to track whether a voucher had been redeemed.

CREATE TABLE vouchers (
    voucher_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL NOT NULL,
    buyer_email TEXT NOT NULL,
    redeemed BOOLEAN DEFAULT 0
);
3. Sales Table
Every transaction had to be recorded, linking both the booth and the voucher involved. We decided to use foreign keys to ensure referential integrity, preventing any orphan records in the sales table.

CREATE TABLE sales (
    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
    voucher_id INTEGER,
    booth_id INTEGER,
    sale_amount REAL,
    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (voucher_id) REFERENCES vouchers(voucher_id),
    FOREIGN KEY (booth_id) REFERENCES booths(booth_id)
);
The sales table became particularly critical for generating accurate sales logs, which were a major feature for both sellers and admins to track daily revenue.

Query Optimization for Performance
The developers and I had numerous discussions about optimizing database queries. The need to retrieve sales data quickly — especially in a real-time environment where booths were actively redeeming vouchers — necessitated efficient query design.

One example was the query for retrieving the sales log for a specific booth:

SELECT 
    s.sale_id, 
    v.voucher_id, 
    v.buyer_email, 
    s.sale_amount, 
    s.sale_date
FROM 
    sales s
JOIN 
    vouchers v ON s.voucher_id = v.voucher_id
WHERE 
    s.booth_id = ?;
Indexing the booth_id column ensured that these queries would execute swiftly, even as the number of records grew over time.

Working with Data in Real Time
One of the unique challenges of this project was ensuring that the voucher redemption system could handle real-time transactions. Booth operators needed immediate feedback when redeeming vouchers, which meant the database had to process updates and retrieve relevant information without delays.

To manage this, we implemented proper locking mechanisms within the database to avoid race conditions during voucher redemption. This was critical in a multi-user environment where multiple booth operators might be redeeming vouchers simultaneously.

Handling Security: Hashing and Session Management
Security was a significant focus in the database design. Booth operators’ passwords were stored as SHA-256 hashes to prevent unauthorized access, and session management was handled securely using Flask’s session mechanism. Collaborating with the developers on these aspects ensured that user data remained secure throughout the system’s operation.

import hashlib
def hasph_password(password):
    return hashlib.sha256(password.encode()).hexdigest()
Future-Proofing the Database
While the system was built to meet the current needs of sellers and administrators, we also considered potential future enhancements during the design process. Scalability was one area we focused on, especially if the system were to grow to handle hundreds of booths and thousands of vouchers. Optimizing table indexing, considering migration to a more powerful database (like PostgreSQL), and ensuring a clear path for schema evolution were all part of our long-term strategy.

Conclusion
The E-Voucher System was a truly collaborative effort between software developers and the database team. By focusing on efficient schema design, query optimization, and security, we were able to deliver a database solution that supported the application’s key features and ensured a seamless user experience for both booth operators and administrators.

Our work provided the foundation for a robust application that manages voucher creation, redemption, and sales tracking, and I’m excited to see how the system will evolve with future enhancements like advanced reporting and mobile responsiveness. As a data analyst and DBA, the E-Voucher System stands out as a rewarding project that highlighted the importance of teamwork, communication, and attention to detail in building a scalable, reliable database architecture.
Source Code is available here
