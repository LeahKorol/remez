import React from "react";
import { useParams } from "react-router-dom";

function Welcome() {
    const { username } = useParams<{ username: string }>();

    return (
        <div style={{ textAlign: "center", marginTop: "50px" }}>
            <h1>ברוך הבא, {username}!</h1>
        </div>
    );
}

export default Welcome;
