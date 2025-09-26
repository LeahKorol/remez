import React from 'react';
import { FaUser, FaSignOutAlt, FaArrowRight } from 'react-icons/fa';
import SavedQueriesList from './SavedQueriesList';
import '../Pages/UserProfile.css';

const Sidebar = ({
    user,
    savedQueries,
    onViewQuery,
    onEditQuery,
    onDeleteQuery,
    onNewQuery,
    showLogoutConfirm,
    showLogoutPopup,
    handleLogoutClick,
    handleLogout
}) => {
    return (
        <div className="sidebar">
            {showLogoutConfirm && (
                <>
                    <div className="logout-popup-overlay"></div>
                    <div className="logout-popup">
                        <img
                            src="logout.png"
                            alt="Logging out"
                            style={{ width: '250px', height: 'auto' }}
                        />
                        <h3>
                            {showLogoutPopup
                                ? "Logging out..."
                                : "Are you sure you want to log out?"}
                        </h3>
                        <div className="confirm-buttons">
                            <button
                                className="confirm-yes"
                                onClick={() => {
                                    handleLogout();
                                }}
                            >
                                Yes
                            </button>
                            <button
                                className="confirm-no"
                                onClick={() => handleLogoutClick(false)}
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </>
            )}

            <div className="logout-container">
                <button className="logout-button" onClick={handleLogoutClick} title="Logout">
                    <FaSignOutAlt />
                </button>
            </div>
            <div className="user-info">
                <div className="avatar-circle">
                    <FaUser className="user-icon" />
                </div>
                <h3 className="user-name">{user.name}</h3>
                <p className="user-email">{user.email}</p>
            </div>

            <div className="saved-queries-section">
                <h2 className="section-title">Your Queries</h2>
                <SavedQueriesList
                    savedQueries={savedQueries}
                    onViewQuery={onViewQuery}
                    onEditQuery={onEditQuery}
                    onDeleteQuery={onDeleteQuery}
                />
            </div>

            <div className="nav-buttons">
                <button className="nav-button" onClick={onNewQuery}>
                    <span>New Query</span>
                    <FaArrowRight />
                </button>
            </div>
        </div>
    );
};

export default Sidebar;