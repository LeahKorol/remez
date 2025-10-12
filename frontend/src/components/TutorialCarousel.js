import React, { useEffect, useState } from "react";
import './TutorialCarousel.css';
import { FaChevronDown, FaChevronLeft, FaChevronRight, FaTimes } from 'react-icons/fa';

const steps = [
    {
        title: "Welcome to REMEZ",
        text: `This quick walkthrough will show you how to run an interaction analysis. You can open this tutorial anytime using the "?" icon on the bottom-right of the User page.`,
        img: "step-welcome.png",
    },
    {
        title: "Create a Query (optional name)",
        text: `Here you may enter a name for your query (optional). This helps you find it later in the saved queries list.`,
        img: "step-name.png",
    },
    {
        title: "Select Period: Start / End Year & Quarter",
        text: `Enter a start year and an end year (allowed range: 2020–2025). Quarters must be 1–4. The start period must be equal to or before the end period.`,
        img: "step-period.png",
    },
    {
        title: "Add Drugs",
        text: `Type at least 3 characters to search the drug database. Select the matching item from the suggestions to attach the drug to your query.`,
        img: "step-drug.png",
    },
    {
        title: "Add Adverse Reactions",
        text: `Same rule as drugs: type 3+ characters and choose from suggestions. You can add multiple reactions.`,
        img: "step-reaction.png",
    },
    {
        title: "Save & Calculate",
        text: `After all required fields are valid, click SAVE + CALC. The system will run the analysis based on Dr. Boris Gorelik's research and email you results including a graph once ready.`,
        img: "step-save.png",
    },
    {
        title: "Error Handling",
        text: `If something goes wrong the application will show an error message (network/server errors might return 404 / 500). Fix the indicated issues and try again.`,
        img: "/assets/tutorial/step-error.png",
    },
    {
        title: "Saved Queries List",
        text: `Your saved queries appear here. Use View / Edit / Delete actions. You can also export results later as CSV or image, or view them as a table.`,
        img: "step-saved-list.png",
    },
    {
        title: "View Query Details",
        text: `Click “View” on a saved query to open its full details, including the drugs, reactions, and analysis results.`,
        img: "step-view-query.png",
    },
    {
        title: "Edit an Existing Query",
        text: `Press “Edit” to modify a query. You can change its parameters, then re-run the analysis and save the updated version.`,
        img: "/assets/tutorial/step-edit-query.png",
    },
    {
        title: "Delete a Query",
        text: `If you no longer need a saved query, click “Delete”. You’ll be asked to confirm before the data is removed.`,
        img: "/assets/tutorial/step-delete-query.png",
    },
    {
        title: "Logout",
        text: `You can log out safely at any time using the logout button located on the sidebar. This will securely end your session and return you to the login page.`,
        img: "step-logout.png",
    },
    {
        title: "Session Expired",
        text: `If you stay inactive for too long, your session will expire automatically for security reasons. You’ll be redirected to the login page with a short message asking you to sign in again.`,
        img: "step-session-expired.png",
    },    
    {
        title: "That's it — You're Ready",
        text: `Press 'Got it' to close the tutorial and start using REMEZ. You can reopen the walkthrough anytime with the "?" icon.`,
        img: "step-done.png",
    }
];

export default function TutorialCarousel({ open, onClose }) {
    const [index, setIndex] = useState(0);

    useEffect(() => {
        if (open) setIndex(0);
    }, [open]);

    useEffect(() => {
        const handleKey = (e) => {
            if (!open) return;
            if (e.key === 'ArrowRight') goNext();
            if (e.key === 'ArrowLeft') goPrev();
            if (e.key === 'Escape') onClose(); // ESC acts as Skip/close
        };
        window.addEventListener('keydown', handleKey);
        return () => window.removeEventListener('keydown', handleKey);
    }, [open, index]);

    const goNext = () => {
        setIndex((i) => Math.min(i + 1, steps.length - 1));
    };

    const goPrev = () => {
        setIndex((i) => Math.max(i - 1, 0));
    };

    if (!open) return null;

    return (
        <div className="tutorial-overlay" role="dialog" aria-modal="true" aria-label="Tutorial">
            <div className="tutorial-container" onClick={(e) => e.stopPropagation()}>
                <header className="tutorial-header">
                    <h3>{steps[index].title}</h3>
                    <button className="tutorial-close" onClick={onClose} aria-label="Close tutorial">
                        <FaTimes />
                    </button>
                </header>

                <div className="tutorial-body">
                    <div className="tutorial-image-wrap">
                        <img
                            src={steps[index].img}
                            alt={steps[index].title}
                            onError={(e) => { e.target.src = '/assets/tutorial/placeholder.png'; }}
                        />
                    </div>

                    <div className="tutorial-text">
                        <div className="tutorial-text-content">
                            {steps[index].text}
                        </div>

                        <div className="tutorial-controls">
                            <button
                                className="tutorial-btn muted"
                                onClick={onClose}
                            >
                                Skip
                            </button>

                            <div className="tutorial-nav">
                                <button
                                    className="icon-btn"
                                    onClick={goPrev}
                                    disabled={index === 0}
                                    aria-label="Previous"
                                >
                                    <FaChevronLeft />
                                </button>

                                <span className="progress">{index + 1} / {steps.length}</span>

                                {index < steps.length - 1 ? (
                                    <button
                                        className="icon-btn primary"
                                        onClick={goNext}
                                        aria-label="Next"
                                    >
                                        <FaChevronRight />
                                    </button>
                                ) : (
                                    <button
                                        className="tutorial-btn primary"
                                        onClick={onClose}
                                        aria-label="Got it"
                                    >
                                        Got it
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>

                </div>

                <footer className="tutorial-footer">
                    <small>For more details see the documentation or contact your research team.</small>
                </footer>
            </div>
        </div>
    );
}