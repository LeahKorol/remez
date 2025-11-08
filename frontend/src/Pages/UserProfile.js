import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { fetchWithRefresh } from '../utils/tokenService';
import QueryDetailsView from "../components/QueryDetailsView";
import { useUser } from "../utils/UserContext";
import { validateQueryForm } from '../utils/formValidation';
import Sidebar from '../components/Sidebar';
import ToastNotification from '../components/ToastNotification';
import QueryForm from '../components/QueryForm';
import TutorialCarousel from '../components/TutorialCarousel';
import './UserProfile.css';


import zoomPlugin from 'chartjs-plugin-zoom';
import {
    Chart as ChartJS,
    LineController,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler,
} from 'chart.js';

ChartJS.register(
    LineController,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler,
    zoomPlugin,
);

const UserProfile = () => {
    // form state
    const [drugs, setDrugs] = useState([{ name: '', id: null }]);
    const [reactions, setReactions] = useState([{ name: '', id: null }]);
    const [yearStart, setYearStart] = useState('');
    const [yearEnd, setYearEnd] = useState('');
    const [quarterStart, setQuarterStart] = useState('');
    const [quarterEnd, setQuarterEnd] = useState('');
    const [queryName, setQueryName] = useState('New Query');

    // search results state
    const [drugSearchResults, setDrugSearchResults] = useState([]);
    const [reactionSearchResults, setReactionSearchResults] = useState([]);
    const [activeDrugSearchIndex, setActiveDrugSearchIndex] = useState(null);
    const [activeReactionSearchIndex, setActiveReactionSearchIndex] = useState(null);

    // search timeout refs (for debouncing)
    const drugSearchTimeout = useRef(null);
    const reactionSearchTimeout = useRef(null);

    // user and queries state
    const [user, setUser] = useState(null);
    const [savedQueries, setSavedQueries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isEditing, setIsEditing] = useState(false);
    const [editingQueryId, setEditingQueryId] = useState(null);
    const [showLogoutPopup, setShowLogoutPopup] = useState(false);
    const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [submitError, setSubmitError] = useState('');
    const [globalLoading, setGlobalLoading] = useState(false);
    const [showTutorial, setShowTutorial] = useState(false);
    const [deleteQueryId, setDeleteQueryId] = useState(null);
    const [showDeletePopup, setShowDeletePopup] = useState(false);

    const [viewMode, setViewMode] = useState('new');
    const [viewingQuery, setViewingQuery] = useState(null);
    const [viewingQueryId, setViewingQueryId] = useState(null);

    const [showToast, setShowToast] = useState(false);
    const [toastMessage, setToastMessage] = useState('');

    const [zoomLevel, setZoomLevel] = useState(1);
    const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
    const [resetFormTrigger, setResetFormTrigger] = useState(0);
    const [isButtonLoading, setIsButtonLoading] = useState(false);
    const [toasts, setToasts] = useState([]);

    // Lock editing/deleting for queries that are in progress
    const isQueryLocked = (query) => {
        const status = query?.result?.status;
        // if this is the query being edited, allow editing
        if (editingQueryId && query.id === editingQueryId) return false;
        return status && status !== "completed" && status !== "failed";
    };

    const navigate = useNavigate();
    const location = useLocation();
    const { userId } = useUser();

    // Handle input changes for year and quarter fields
    const handleInputChange = (e) => {
        const { name, value } = e.target;
        switch (name) {
            case 'startYear':
                setYearStart(value);
                break;
            case 'endYear':
                setYearEnd(value);
                break;
            case 'startQuarter':
                setQuarterStart(value);
                break;
            case 'endQuarter':
                setQuarterEnd(value);
                break;
            case 'queryName':
                setQueryName(value);
                break;
            default:
                break;
        }
    };

    useEffect(() => {
        const fetchUserData = async () => {
            setLoading(true);
            setError(null);

            const token = localStorage.getItem('token');
            if (!token) {
                navigate('/session-expired'); // session expired
                return;
            }

            try {
                const userResponse = await fetchWithRefresh('http://127.0.0.1:8000/api/v1/auth/user/', {
                    method: 'GET'
                });

                if (!userResponse) {
                    setError('Unable to connect to server. Please try again later.');
                    return;
                }

                if (userResponse.status === 401) {
                    localStorage.removeItem('token');
                    navigate('/session-expired'); // session expired
                    return;
                }

                if (userResponse.status >= 500) {
                    setError('Server error. Please try again later.');
                    navigate('/500');
                    return;
                }

                if (!userResponse.ok) {
                    setError(`Failed to load user data: ${userResponse.status}`);
                    navigate('/not-found');
                    return;
                }

                const userData = await userResponse.json();
                const userName = userData.name || userData.email?.split('@')[0] || 'User';
                setUser({ ...userData, name: userName });

                await fetchQueries(); // fetch queries after user loaded
            } catch (err) {
                console.error('Unexpected error fetching user data:', err);
                setError('Unexpected error occurred. Please check your connection.');
            } finally {
                setLoading(false);
            }
        };

        fetchUserData();
    }, []);


    const fetchQueries = async () => {
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                console.log('No token for queries');
                navigate('/session-expired'); // session expired
                return;
            }

            const response = await fetchWithRefresh('http://127.0.0.1:8000/api/v1/analysis/queries/', {
                method: 'GET'
            });

            if (!response) {
                setError('Unable to connect to server. Please try again later.');
                return;
            }

            if (response.status === 401) {
                localStorage.removeItem('token');
                navigate('/session-expired'); // session expired
                return;
            }

            if (response.status >= 500) {
                navigate('/500');
                return;
            }

            if (response.status === 404) {
                navigate('/not-found');
                return;
            }

            if (!response.ok) {
                setError(`Failed to load queries: ${response.status}`);
                return;
            }

            const data = await response.json();

            // Sort queries: results first, then by creation date descending
            const sortedQueries = data.sort((a, b) => {
                const aHasResults = a.result && a.result.ror_values && a.result.ror_values.length > 0;
                const bHasResults = b.result && b.result.ror_values && b.result.ror_values.length > 0;

                if (aHasResults && !bHasResults) return -1;
                if (!aHasResults && bHasResults) return 1;

                return new Date(b.created_at) - new Date(a.created_at);
            });

            setSavedQueries(sortedQueries);
        } catch (err) {
            console.error('Unexpected error fetching queries:', err);
            setError('Unexpected error occurred. Please check your connection.');
        }
    };


    // Handle viewing a saved query
    const handleViewQuery = async (query) => {
        setViewMode('view');
        setViewingQueryId(query.id);
        setViewingQuery(null);

        try {
            const token = localStorage.getItem('token');
            const res = await fetchWithRefresh(`http://127.0.0.1:8000/api/v1/analysis/queries/${query.id}/`);
            if (!res.ok) throw new Error('Failed to fetch full query');
            const fullQuery = await res.json();
            setViewingQuery(fullQuery);
        } catch (err) {
            console.error('Error fetching full query:', err);
            alert('Failed to load query details. Please try again.');
            setViewMode('new');
            setViewingQueryId(null);
        }
    };

    const createLabelsForActualData = (query) => {
        const dataLength = query.ror_values ? query.ror_values.length : 0;

        if (dataLength === 0) {
            return [];
        }

        // if there is only one data point, return just that period
        if (dataLength === 1) {
            return [`${query.year_start} Q${query.quarter_start}`];
        }

        // create labels based on actual data length
        const labels = [];
        let currentYear = query.year_start;
        let currentQuarter = query.quarter_start;

        for (let i = 0; i < dataLength; i++) {
            labels.push(`${currentYear} Q${currentQuarter}`);

            // pass to the next quarter
            currentQuarter++;
            if (currentQuarter > 4) {
                currentQuarter = 1;
                currentYear++;
            }
        }

        return labels;
    };

    // Search for drugs as the user types
    const searchDrugs = async (prefix, index) => {
        // Only if there are at least 3 characters do the search take place
        if (!prefix.trim() || prefix.trim().length < 3) {
            setDrugSearchResults([]);
            setActiveDrugSearchIndex(null);
            return;
        }

        try {
            const response = await fetchWithRefresh(`http://127.0.0.1:8000/api/v1/analysis/drug-names/search/${prefix}/`);

            if (!response) {
                setDrugSearchResults([]);
                return;
            }

            if (response.ok) {
                const data = await response.json();
                setDrugSearchResults(data);
                setActiveDrugSearchIndex(index);
            } else {
                console.error('Error fetching drug search results:', response.statusText);
                setDrugSearchResults([]);
            }

        } catch (error) {
            console.error('Error fetching drug search results:', error);
            setDrugSearchResults([]);
        }
    };

    // Handle drug input changes with debouncing
    const handleDrugChange = (index, value) => {
        const newDrugs = [...drugs];
        newDrugs[index] = { name: value || '', id: null }; // ensure it isn't undefined
        setDrugs(newDrugs);

        // Debounce the search API call
        if (drugSearchTimeout.current) {
            clearTimeout(drugSearchTimeout.current);
        }

        drugSearchTimeout.current = setTimeout(() => {
            searchDrugs(value, index);
        }, 300);
    };

    // Select a drug from search results
    const selectDrug = (drug) => {
        if (activeDrugSearchIndex === null) return;

        const newDrugs = [...drugs];
        newDrugs[activeDrugSearchIndex] = { name: drug.name, id: drug.id };
        setDrugs(newDrugs);
        setDrugSearchResults([]);
        setActiveDrugSearchIndex(null);
    };

    const searchReactions = async (prefix, index) => {
        if (!prefix.trim() || prefix.trim().length < 3) {
            setReactionSearchResults([]);
            setActiveReactionSearchIndex(null);
            return;
        }

        try {
            const response = await fetchWithRefresh(`http://127.0.0.1:8000/api/v1/analysis/reaction-names/search/${prefix}/`);

            if (!response) {
                setReactionSearchResults([]);
                return;
            }

            if (response.ok) {
                const data = await response.json();
                setReactionSearchResults(data);
                setActiveReactionSearchIndex(index);
            } else {
                console.error('Error fetching reaction search results:', response.statusText);
                setReactionSearchResults([]);
            }
        } catch (error) {
            console.error('Error fetching reaction search results:', error);
            setReactionSearchResults([]);
        }
    };

    const selectReaction = (reaction) => {
        if (activeReactionSearchIndex === null) return;

        const newReactions = [...reactions];
        newReactions[activeReactionSearchIndex] = { name: reaction.name, id: reaction.id };
        setReactions(newReactions);
        setReactionSearchResults([]);
        setActiveReactionSearchIndex(null);
    };

    // // Get CSRF token from cookies
    // const getCSRFToken = () => {
    //     const cookies = document.cookie.split('; ');
    //     const csrfCookie = cookies.find(cookie => cookie.startsWith('csrftoken='));
    //     return csrfCookie ? csrfCookie.split('=')[1] : null;
    // };

    const resetForm = () => {
        setDrugs([{ name: '', id: null }]);
        setReactions([{ name: '', id: null }]);
        setYearStart('');
        setYearEnd('');
        setQuarterStart('');
        setQuarterEnd('');
        setQueryName('New Query');
        setIsEditing(false);
        setEditingQueryId(null);
    };

    const showToastMessage = (message, type = "info") => {
        const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
        setToasts((prev) => [...prev, { id, message, type }]);
    };

    const handleSubmitQuery = async (FormData) => {
        setIsButtonLoading(true);
        const { queryName, yearStart, yearEnd, quarterStart, quarterEnd, drugs, reactions } = FormData;

        if (!queryName) {
            console.error("FormData missing, did you call handleSubmitQuery without data?");
            return;
        }

        if (isEditing) {
            const original = savedQueries.find(q => q.id === editingQueryId);
            if (original && isQueryLocked(original)) {
                showToastMessage("Cannot update query while processing." , "error");
                setIsSubmitting(false);
                setGlobalLoading(false);
                return;
            }
        }

        setIsSubmitting(true);
        setGlobalLoading(true);
        setSubmitError('');

        const errors = validateQueryForm({
            drugs,
            reactions,
            yearStart,
            yearEnd,
            quarterStart,
            quarterEnd,
            queryName,
        });

        if (errors.length > 0) {
            errors.forEach(err => showToastMessage(err));
            setIsSubmitting(false);
            setGlobalLoading(false);
            return;
        }

        try {
            const token = localStorage.getItem('token');
            if (!token) {
                navigate('/session-expired'); // session expired
                return;
            }

            const payload = {
                name: queryName,
                year_start: parseInt(yearStart),
                year_end: parseInt(yearEnd),
                quarter_start: parseInt(quarterStart),
                quarter_end: parseInt(quarterEnd),
                drugs: drugs.filter(d => d.id).map(d => d.id),
                reactions: reactions.filter(r => r.id).map(r => r.id),
                user_id: userId
            };

            let response;
            if (editingQueryId) {
                response = await axios.put(
                    `http://127.0.0.1:8000/api/v1/analysis/queries/${editingQueryId}/`,
                    payload,
                    { headers: { Authorization: `Bearer ${token}` } }
                );
            } else {
                response = await axios.post(
                    'http://127.0.0.1:8000/api/v1/analysis/queries/',
                    payload,
                    { headers: { Authorization: `Bearer ${token}` } }
                );
            }

            const newQuery = response.data;
            console.log("newQuery: ", newQuery);

            if (editingQueryId) {
                setSavedQueries(prev => prev.map(q => q.id === newQuery.id ? newQuery : q));
                showToastMessage('Query updated successfully!', "success");
            } else {
                setSavedQueries(prev => [newQuery, ...prev]);
                showToastMessage('Query saved successfully!', "success");
                resetForm();
            }

            navigate('/loading', {
                state: { queryData: newQuery, isUpdate: !!editingQueryId }
            });

        } catch (error) {
            console.error('Error saving query:', error);

            if (error.response) {
                if (error.response.status === 401) {
                    localStorage.removeItem('token');
                    navigate('/session-expired'); // session expired
                    return;
                }

                if (error.response.status >= 500) {
                    navigate('/500');
                    return;
                }

                if (error.response.status === 404) {
                    navigate('/not-found');
                    return;
                }

                setSubmitError(error.response.data?.detail || 'Failed to save query');
            } else {
                setSubmitError('Network error: Unable to connect to server.');
            }
        } finally {
            setIsSubmitting(false);
            setGlobalLoading(false);
            setIsButtonLoading(false);
        }
    };

    // Add useEffect to handle success messages and updated queries from loading page
    useEffect(() => {
        const state = location.state;
        if (state?.message && state?.type === 'success') {
            showToastMessage(state.message);

            // if there is an updated query, view it
            if (state.updatedQuery) {
                console.log("Received updated query from loading:", state.updatedQuery);

                // update the saved queries list
                setSavedQueries(prevQueries =>
                    prevQueries.map(q =>
                        q.id === state.updatedQuery.id ? state.updatedQuery : q
                    )
                );

                // view the updated query
                setViewMode('view');
                setViewingQuery(state.updatedQuery);

                // scrolling to top to see the details
                setTimeout(() => {
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                }, 100);
            }

            // clean the state to prevent re-showing on refresh
            window.history.replaceState({}, document.title);
        }
    }, [location.state]);

    // Handle deleting a query
    const handleDeleteQuery = async (queryId) => {
        setDeleteQueryId(queryId);
        setShowDeletePopup(true);
    };

    const confirmDeleteQuery = async () => {
        setIsButtonLoading(true);

        if (!deleteQueryId) return;

        try {
            const token = localStorage.getItem('token');
            if (!token) {
                alert('You are not logged in. Please log in first.');
                navigate('/session-expired');
                return;
            }

            const response = await fetchWithRefresh(`http://127.0.0.1:8000/api/v1/analysis/queries/${deleteQueryId}/`, {
                method: 'DELETE'
            });

            if (response && (response.ok || response.status === 204)) {
                setSavedQueries(savedQueries.filter(q => q.id !== deleteQueryId));
                showToastMessage('Query deleted successfully!', "success");

                if (viewMode === 'view' && viewingQueryId === deleteQueryId) {
                    // If currently viewing the deleted query, reset to new query form
                    setViewMode('new');
                    setViewingQuery(null);
                    setViewingQueryId(null);
                    resetForm();
                    setResetFormTrigger(prev => prev + 1);
                }
            } else {
                alert('Failed to delete query');
            }
        } catch (error) {
            console.error('Error deleting query:', error);
            alert('Network error: Unable to delete query.');
        } finally {
            setDeleteQueryId(null);
            setShowDeletePopup(false);
            setIsButtonLoading(false);
        }
    };

    const cancelDelete = () => {
        setDeleteQueryId(null);
        setShowDeletePopup(false);
    };


    // Add a new drug field
    const addDrugField = () => {
        setDrugs([...drugs, { name: '', id: null }]);
    };

    const removeDrugField = (index) => {
        if (drugs.length > 1) {
            const newDrugs = [...drugs];
            newDrugs.splice(index, 1);
            setDrugs(newDrugs);
        }
    };

    // reactions management functions
    const handleReactionChange = (index, value) => {
        const newReactions = [...reactions];
        newReactions[index] = { name: value || '', id: null }; // Ensure it's not undefined
        setReactions(newReactions);

        if (reactionSearchTimeout.current) {
            clearTimeout(reactionSearchTimeout.current);
        }

        reactionSearchTimeout.current = setTimeout(() => {
            searchReactions(value, index);
        }, 300);
    };

    const addReactionField = () => {
        setReactions([...reactions, { name: '', id: null }]);
    };

    const removeReactionField = (index) => {
        if (reactions.length > 1) {
            const newReactions = [...reactions];
            newReactions.splice(index, 1);
            setReactions(newReactions);
        }
    };

    const handleEditQuery = async (query) => {
        setViewMode('edit');
        setViewingQuery(null);
        // setIsEditing(true);
        setEditingQueryId(query.id);
        setLoading(true);

        try {
            const token = localStorage.getItem('token');
            if (!token) {
                alert('You are not logged in. Please log in first.');
                navigate('/session-expired');
                return;
            }

            const response = await fetchWithRefresh(`http://127.0.0.1:8000/api/v1/analysis/queries/${query.id}/`);

            if (!response) {
                alert('Failed to load query data for editing');
                resetForm();
                return;
            }

            const queryData = await response.json();
            console.log('Query data from backend:', queryData);

            const drugsToEdit = (queryData.drugs_details || []).map(d => ({
                id: d.id ?? null,
                name: d.name ?? ''
            }));

            const reactionsToEdit = (queryData.reactions_details || []).map(r => ({
                id: r.id ?? null,
                name: r.name ?? ''
            }));

            setDrugs(drugsToEdit.length > 0 ? drugsToEdit : [{ name: '', id: null }]);
            setReactions(reactionsToEdit.length > 0 ? reactionsToEdit : [{ name: '', id: null }]);

            setYearStart(queryData.year_start ? queryData.year_start.toString() : '');
            setYearEnd(queryData.year_end ? queryData.year_end.toString() : '');
            setQuarterStart(queryData.quarter_start ? queryData.quarter_start.toString() : '');
            setQuarterEnd(queryData.quarter_end ? queryData.quarter_end.toString() : '');
            setQueryName(queryData.name || 'New Query');

            setIsEditing(true);

            window.scrollTo({ top: 0, behavior: 'smooth' });
        } catch (error) {
            console.error('Error loading query for editing:', error);
            alert('Failed to load query data for editing');
            resetForm();
        } finally {
            setLoading(false);
        }
    };

    const cancelEditing = () => {
        resetForm();
        setResetFormTrigger(prev => prev + 1);
        setIsEditing(false);
        setEditingQueryId(null);
        setViewMode('new');
    };

    const handleNewQuery = () => {
        setResetFormTrigger(prev => prev + 1);
        setViewMode('new');
        setViewingQuery(null);
        resetForm();
    };

    const handleLogoutClick = () => {
        setShowLogoutConfirm(true);
    };

    const handleLogout = async () => {
        setShowLogoutPopup(true);
        await new Promise(resolve => setTimeout(resolve, 750));
        try {
            const response = await fetch('http://127.0.0.1:8000/api/v1/auth/logout/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                localStorage.removeItem('token');  // remove the token from local storage
                setShowLogoutPopup(false);
                navigate('/');  // go to home page
            } else {
                const data = await response.json();
                console.error('Logout failed:', data.message || 'Something went wrong');
                alert('An error occurred while logging out');
            }
        } catch (error) {
            console.error('Network error during logout:', error);
            alert('Network error during logout');
            setShowLogoutPopup(false);
        }
    };

    if (loading) {
        return <div className="loading">Loading...</div>;
    }

    if (error) {
        return <div className="error">{error}</div>;
    }

    if (!user) {
        return <div className="not-logged-in">Log in to view your profile</div>;
    }

    const refreshQuery = async (queryId) => {
        try {
            const response = await fetchWithRefresh(
                `http://127.0.0.1:8000/api/v1/analysis/queries/${queryId}/`,
                { method: 'GET' }
            );

            if (!response.ok) {
                console.error("Failed to refresh query:", response.status);
                return null;
            }

            const data = await response.json();
            return data;
        } catch (err) {
            console.error("Error refreshing query:", err);
            return null;
        }
    };

    return (
        <div className="user-profile-container">
            <div className="main-content">
                <div className="prompt-container">
                    {viewMode === 'view' && viewingQuery ? (
                        <QueryDetailsView
                            query={viewingQuery}
                            handleNewQuery={handleNewQuery}
                            refreshQuery={refreshQuery}
                        />
                    ) : (
                        <>
                            <div className="form-header">
                                <h2>{isEditing ? 'Update Query' : 'New Query'}</h2>
                                <button
                                    type="button"
                                    className="cancel-button"
                                    onClick={cancelEditing}
                                >
                                    Cancel
                                </button>

                                <div className="toast-container">
                                    {toasts.map((toast, index) => (
                                        <ToastNotification
                                            key={toast.id}
                                            id={toast.id}
                                            message={toast.message}
                                            type={toast.type}
                                            duration={8000}
                                            index={index}
                                            onClose={(id) => setToasts((prev) => prev.filter((t) => t.id !== id))}
                                        />
                                    ))}
                                </div>
                            </div>

                            <QueryForm
                                drugs={drugs}
                                reactions={reactions}
                                yearStart={yearStart}
                                yearEnd={yearEnd}
                                quarterStart={quarterStart}
                                quarterEnd={quarterEnd}
                                queryName={queryName}
                                isEditing={isEditing}
                                isSubmitting={isSubmitting}
                                submitError={submitError}
                                showToastMessage={showToastMessage}
                                onSubmit={handleSubmitQuery}
                                onCancel={cancelEditing}
                                onDrugChange={handleDrugChange}
                                onReactionChange={handleReactionChange}
                                addDrug={addDrugField}
                                addReaction={addReactionField}
                                removeDrug={removeDrugField}
                                removeReaction={removeReactionField}
                                activeDrugSearchIndex={activeDrugSearchIndex}
                                activeReactionSearchIndex={activeReactionSearchIndex}
                                drugSearchResults={drugSearchResults}
                                reactionSearchResults={reactionSearchResults}
                                resetTrigger={resetFormTrigger}
                                isLocked={isEditing && viewingQuery && isQueryLocked(viewingQuery)}
                            />

                        </>
                    )}
                </div>
            </div>

            <Sidebar
                user={user}
                savedQueries={savedQueries}
                onViewQuery={handleViewQuery}
                onEditQuery={(query) => handleEditQuery(query)}
                onDeleteQuery={(query) => handleDeleteQuery(query)}
                onNewQuery={handleNewQuery}
                showLogoutConfirm={showLogoutConfirm}
                showLogoutPopup={showLogoutPopup}
                handleLogoutClick={handleLogoutClick}
                handleLogout={handleLogout}
                editingQueryId={editingQueryId}
                isEditing={isEditing}
                editingQueryLoading={loading && viewMode === 'edit'}
                viewingQueryId={viewingQueryId}
            />

            <button
                className="help-button"
                onClick={() => setShowTutorial(true)}
                aria-label="Open tutorial"
            >
                ?
            </button>

            <TutorialCarousel
                open={showTutorial}
                onClose={() => setShowTutorial(false)}
            />

            {showDeletePopup && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <img src="images/delete-icon.png" alt="Delete" className="modal-icon" />
                        <h3>Delete Query</h3>
                        <p>Are you sure you want to delete this query?</p>
                        <div className="modal-buttons">
                            <button
                                className="confirm-button"
                                disabled={isButtonLoading}
                                onClick={confirmDeleteQuery}
                            >
                                {isButtonLoading ? <div className="spinner"></div> : 'Delete'}
                            </button>
                            <button
                                className="cancel-button"
                                onClick={cancelDelete}>
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default UserProfile;