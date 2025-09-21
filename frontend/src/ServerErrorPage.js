import React from "react";

export default function ServerErrorPage() {
    const currentYear = new Date().getFullYear();

    return (
        <div style={{ fontFamily: "'Poppins', sans-serif", minHeight: "100vh", display: "flex", flexDirection: "column", textAlign: "center", backgroundColor: "#f9f9fb", color: "#333" }}>

            {/* Navbar */}
            <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "15px 30px", borderBottom: "1px solid #f0f0f0", backgroundColor: "#fff" }}>
                <div style={{ fontWeight: "bold", fontSize: "24px", background: "linear-gradient(90deg, #7b42e0 0%, #5e68f1 100%)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                    REMEZ
                </div>
            </header>

            {/* Main content */}
            <main style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", padding: "40px 20px" }}>
                
                <img
                    src="500.png"
                    alt="500 status"
                    style={{ width: "450px", maxWidth: "90%", marginBottom: "30px", display: "block", marginLeft: "auto", marginRight: "auto" }}
                />

                <p style={{ fontSize: "18px", color: "#666", marginBottom: "30px" }}>
                    Oops! Something went wrong on our end. Please try again later.
                </p>
                <a href="/" style={{ backgroundColor: "#111827", color: "white", textDecoration: "none", padding: "12px 25px", borderRadius: "5px", fontWeight: 600, transition: "background 0.2s" }}
                    onMouseEnter={e => e.currentTarget.style.backgroundColor = "#1f2937"}
                    onMouseLeave={e => e.currentTarget.style.backgroundColor = "#111827"}>
                    Back to Home
                </a>
            </main>

            {/* Footer */}
            <footer style={{ marginTop: "auto", color: "#888", fontSize: "12px", padding: "20px", backgroundColor: "#fff", borderTop: "1px solid #f0f0f0" }}>
                &copy; {currentYear} REMEZ. All rights reserved.
            </footer>
        </div>
    );
}
