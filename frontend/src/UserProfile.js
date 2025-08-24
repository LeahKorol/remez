import React, { useState, useEffect, useRef } from 'react';
import { FaUser, FaArrowRight, FaPlus, FaTimes, FaEdit, FaTrash, FaSignOutAlt, FaChevronDown, FaEye } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
// import { fetchWithRefresh } from './Login';
import './UserProfile.css';

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
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [submitError, setSubmitError] = useState('');

    const [viewMode, setViewMode] = useState('new');
    const [viewingQuery, setViewingQuery] = useState(null);

    const [showToast, setShowToast] = useState(false);
    const [toastMessage, setToastMessage] = useState('');

    const navigate = useNavigate();

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

    // fetch user data on component mount
    useEffect(() => {
        const fetchUserData = async () => {
            try {
                setLoading(true);
                const token = localStorage.getItem('token');
                console.log('token:', token);

                if (!token) {
                    console.log('No token found, redirecting to login');
                    navigate('/');
                    return;
                }

                const userResponse = await fetch('http://127.0.0.1:8000/api/v1/auth/user/', {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                });

                console.log('User response status:', userResponse.status);

                if (userResponse.status === 401) {
                    console.log('Token expired or invalid, redirecting to login');
                    localStorage.removeItem('token');
                    navigate('/');
                    return;
                }

                if (!userResponse.ok) {
                    throw new Error(`Failed to fetch user data: ${userResponse.status}`);
                }

                const userData = await userResponse.json();
                console.log('User data received:', userData);

                const userName = userData.name || userData.email?.split('@')[0] || 'User';
                setUser({ ...userData, name: userName });

                // Fetch queries after user data is successfully loaded
                await fetchQueries();

            } catch (error) {
                console.error('Error fetching user data:', error);
                setError('An error occurred while loading user data');
                // Don't redirect on network errors, only on auth errors
                if (error.message.includes('401') || error.message.includes('unauthorized')) {
                    localStorage.removeItem('token');
                    navigate('/');
                }
            } finally {
                setLoading(false);
            }
        };


        fetchUserData();
    }, []);

    // fetch queries when user data is loaded
    const fetchQueries = async () => {
        try {
            const token = localStorage.getItem('token');

            if (!token) {
                console.log('No token for queries');
                return;
            }

            const response = await fetch('http://127.0.0.1:8000/api/v1/analysis/queries/', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
            });

            console.log('Queries response status:', response.status);

            if (response.status === 401) {
                console.log('Token expired while fetching queries');
                localStorage.removeItem('token');
                navigate('/');
                return;
            }

            if (response.ok) {
                const data = await response.json();
                console.log('Queries loaded:', data.length);
                setSavedQueries(data);
            } else {
                console.error('Failed to fetch queries:', response.status);
                // Don't show error for queries, just log it
            }
        } catch (error) {
            console.error('Error fetching queries:', error);
            // Don't show error for queries, just log it
        }
    };

    // Handle viewing a saved query
    const handleViewQuery = (query) => {
        setViewMode('view');
        setViewingQuery(query);
        setIsEditing(false);
        setEditingQueryId(null);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };


    const QueryDetailsView = ({ query }) => {
        return (
            <div className="query-details-container">
                <div className="form-header">
                    <h2>{query.name}</h2>
                    <div className="query-details-actions">
                        {/* <button
                            type="button"
                            className="edit-button"
                            onClick={() => handleEditQuery(query)}
                        >
                            <FaEdit /> Edit Query
                        </button> */}
                        <button
                            type="button"
                            className="cancel-button"
                            onClick={handleNewQuery}
                        >
                            <FaTimes /> Close
                        </button>
                    </div>
                </div>

                {/* Query Information Section */}
                <div className="query-info-section">
                    <h3>Query Information</h3>
                    <div className="info-grid">
                        <div className="info-item">
                            <span className="info-label">Time Period:</span>
                            <span className="info-value">
                                {query.year_start} Q{query.quarter_start} - {query.year_end} Q{query.quarter_end}
                            </span>
                        </div>
                        <div className="info-item">
                            <span className="info-label">Created:</span>
                            <span className="info-value">
                                {new Date(query.created_at).toLocaleDateString()}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Drugs Section */}
                <div className="query-section">
                    <h3>Drugs ({query.drugs?.length || 0})</h3>
                    <div className="items-list">
                        {query.drugs && query.drugs.length > 0 ? (
                            query.drugs.map((drug, index) => (
                                <div key={index} className="item-tag drug-tag">
                                    {drug.name}
                                </div>
                            ))
                        ) : (
                            <p className="no-items">No drugs specified</p>
                        )}
                    </div>
                </div>

                {/* Reactions Section */}
                <div className="query-section">
                    <h3>Reactions ({query.reactions?.length || 0})</h3>
                    <div className="items-list">
                        {query.reactions && query.reactions.length > 0 ? (
                            query.reactions.map((reaction, index) => (
                                <div key={index} className="item-tag reaction-tag">
                                    {reaction.name}
                                </div>
                            ))
                        ) : (
                            <p className="no-items">No reactions specified</p>
                        )}
                    </div>
                </div>

                {/* Results Section - Placeholder for Chart */}
                <div className="query-section">
                    <h3>Frequency Analysis</h3>
                    <div className="chart-placeholder">
                        <div className="chart-container">
                            <div className="placeholder-content">
                                <div className="placeholder-icon">📊</div>
                                <h4>Chart Coming Soon</h4>
                                <p>Frequency analysis chart will be displayed here</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
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
            const token = localStorage.getItem('token');
            const response = await fetch(`http://127.0.0.1:8000/api/v1/analysis/drug-names/search/${prefix}/`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
            });

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
        newDrugs[index] = { name: value || '', id: null }; // וודא שזה לא undefined
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
            const token = localStorage.getItem('token');
            const response = await fetch(`http://127.0.0.1:8000/api/v1/analysis/reaction-names/search/${prefix}/`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
            });

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

    const showToastMessage = (message) => {
        setToastMessage(message);
        setShowToast(true);
        setTimeout(() => setShowToast(false), 3000);
    };


    // Handle form submission for saving or updating queries
    const handleSubmitQuery = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        setSubmitError('');

        if (!validateForm()) {
            setIsSubmitting(false);
            return;
        }

        try {
            const token = localStorage.getItem('token');

            if (!token) {
                alert('You are not logged in. Please log in first.');
                navigate('/');
                return;
            }

            const payload = {
                name: queryName,
                year_start: parseInt(yearStart),
                year_end: parseInt(yearEnd),
                quarter_start: parseInt(quarterStart),
                quarter_end: parseInt(quarterEnd),
                drugs: drugs.filter(d => d.id).map(d => d.id),
                reactions: reactions.filter(r => r.id).map(r => r.id)
            };

            console.log('Submitting payload:', payload);

            const config = {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            };

            console.log("config: ", config);

            let response;
            if (editingQueryId) {
                response = await axios.put(
                    `http://127.0.0.1:8000/api/v1/analysis/queries/${editingQueryId}/`,
                    payload,
                    config
                );
            } else {
                response = await axios.post(
                    'http://127.0.0.1:8000/api/v1/analysis/queries/',
                    payload,
                    config
                );
            }

            console.log('Submit query response status:', response.status);

            const newQuery = response.data;

            if (editingQueryId) {
                setSavedQueries(savedQueries.map(q => q.id === newQuery.id ? newQuery : q));
                showToastMessage('Query updated successfully!');
            } else {
                setSavedQueries([newQuery, ...savedQueries]);
                showToastMessage('Query saved successfully!');
            }

            resetForm();

        } catch (error) {
            console.error('Error saving query:', error.response?.data || error);

            if (error.response?.status === 401) {
                alert('Your session has expired. Please log in again.');
                localStorage.removeItem('token');
                navigate('/');
            } else {
                const errorMessage = error.response?.data?.detail ||
                    error.response?.data?.message ||
                    'Failed to save query';
                alert(`Error: ${errorMessage}`);
                setSubmitError(errorMessage);
            }
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleDeleteQuery = async (queryId) => {
        if (!window.confirm('Are you sure you want to delete this query?')) {
            return;
        }

        try {
            const token = localStorage.getItem('token');

            if (!token) {
                alert('You are not logged in. Please log in first.');
                navigate('/');
                return;
            }

            console.log('Deleting query with ID:', queryId);

            const response = await fetch(`http://127.0.0.1:8000/api/v1/analysis/queries/${queryId}/`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            console.log('Delete response status:', response.status);

            if (response.status === 401) {
                console.log('Token expired during delete, redirecting to login');
                localStorage.removeItem('token');
                navigate('/');
                return;
            }

            if (response.status === 403) {
                alert('You do not have permission to delete this query.');
                return;
            }

            if (response.status === 404) {
                alert('Query not found. It may have already been deleted.');
                // Refresh queries to sync with server state
                await fetchQueries();
                return;
            }

            if (response.ok || response.status === 204) {
                // Successfully deleted
                setSavedQueries(savedQueries.filter(q => q.id !== queryId));
                showToastMessage('Query deleted successfully!');

                // If we were editing this query, reset the form
                if (editingQueryId === queryId) {
                    resetForm();
                }
            } else {
                // Handle other error responses
                let errorMessage = 'Failed to delete query';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorData.message || errorMessage;
                } catch (parseError) {
                    errorMessage = `Server error (${response.status})`;
                }

                console.error('Error deleting query:', errorMessage);
                alert(`Failed to delete query: ${errorMessage}`);
            }
        } catch (error) {
            console.error('Network error during delete:', error);
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                alert('Network error: Unable to connect to server. Please check your connection.');
            } else {
                alert(`Failed to delete query: ${error.message || 'Network error'}`);
            }
        }
    };


    const CustomSelect = ({ value, onChange, options, placeholder, name }) => {
        const [isOpen, setIsOpen] = useState(false);

        return (
            <div className="custom-select-container">
                <div
                    className="custom-select-header"
                    onClick={() => setIsOpen(!isOpen)}
                >
                    {value ? `Quarter ${value}` : placeholder}
                    <FaChevronDown className={`chevron ${isOpen ? 'open' : ''}`} />
                </div>
                {isOpen && (
                    <div className="custom-select-options">
                        {options.map(option => (
                            <div
                                key={option.value}
                                className="custom-select-option"
                                onClick={() => {
                                    onChange({ target: { name, value: option.value } });
                                    setIsOpen(false);
                                }}
                            >
                                {option.label}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        );
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

    // // Helper function to fetch drug names by IDs
    // const fetchDrugNames = async (drugIds) => {
    //     const token = localStorage.getItem('token');
    //     const drugPromises = drugIds.map(async (drugId) => {
    //         try {
    //             const response = await fetch(`http://127.0.0.1:8000/api/v1/analysis/drug-names/${drugId}/`, {
    //                 headers: {
    //                     'Authorization': `Bearer ${token}`,
    //                     'Content-Type': 'application/json'
    //                 }
    //             });

    //             if (response.ok) {
    //                 const drugData = await response.json();
    //                 return { name: drugData.name, id: drugData.id };
    //             } else {
    //                 console.error(`Failed to fetch drug ${drugId}`);
    //                 return { name: `Drug ID: ${drugId}`, id: drugId }; // Fallback
    //             }
    //         } catch (error) {
    //             console.error(`Error fetching drug ${drugId}:`, error);
    //             return { name: `Drug ID: ${drugId}`, id: drugId }; // Fallback
    //         }
    //     });

    //     return Promise.all(drugPromises);
    // };

    // // Helper function to fetch reaction names by IDs
    // const fetchReactionNames = async (reactionIds) => {
    //     const token = localStorage.getItem('token');
    //     const reactionPromises = reactionIds.map(async (reactionId) => {
    //         try {
    //             const response = await fetch(`http://127.0.0.1:8000/api/v1/analysis/reaction-names/${reactionId}/`, {
    //                 headers: {
    //                     'Authorization': `Bearer ${token}`,
    //                     'Content-Type': 'application/json'
    //                 }
    //             });

    //             if (response.ok) {
    //                 const reactionData = await response.json();
    //                 return { name: reactionData.name, id: reactionData.id };
    //             } else {
    //                 console.error(`Failed to fetch reaction ${reactionId}`);
    //                 return { name: `Reaction ID: ${reactionId}`, id: reactionId }; // Fallback
    //             }
    //         } catch (error) {
    //             console.error(`Error fetching reaction ${reactionId}:`, error);
    //             return { name: `Reaction ID: ${reactionId}`, id: reactionId }; // Fallback
    //         }
    //     });

    //     return Promise.all(reactionPromises);
    // };


    // // Helper function to fetch drug name by ID (adjust endpoint as needed)
    // const fetchDrugById = async (drugId) => {
    //     try {
    //         const token = localStorage.getItem('token');

    //         // נסה את ה-endpoint הנכון לפי ה-API שלך
    //         const response = await fetch(`http://127.0.0.1:8000/api/v1/analysis/drug-names/${drugId}/`, {
    //             headers: {
    //                 'Authorization': `Bearer ${token}`,
    //                 'Content-Type': 'application/json'
    //             }
    //         });

    //         if (response.ok) {
    //             const data = await response.json();
    //             return { name: data.name, id: data.id };
    //         } else if (response.status === 404) {
    //             console.warn(`Drug ${drugId} not found`);
    //             return { name: `Drug ID: ${drugId} (not found)`, id: drugId };
    //         } else {
    //             throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    //         }
    //     } catch (error) {
    //         console.error(`Error fetching drug ${drugId}:`, error);
    //         return { name: `Drug ID: ${drugId}`, id: drugId };
    //     }
    // };

    // // Helper function to fetch reaction name by ID (adjust endpoint as needed)
    // const fetchReactionById = async (reactionId) => {
    //     try {
    //         const token = localStorage.getItem('token');

    //         // נסה את ה-endpoint הנכון לפי ה-API שלך
    //         const response = await fetch(`http://127.0.0.1:8000/api/v1/analysis/reaction-names/${reactionId}/`, {
    //             headers: {
    //                 'Authorization': `Bearer ${token}`,
    //                 'Content-Type': 'application/json'
    //             }
    //         });

    //         if (response.ok) {
    //             const data = await response.json();
    //             return { name: data.name, id: data.id };
    //         } else if (response.status === 404) {
    //             console.warn(`Reaction ${reactionId} not found`);
    //             return { name: `Reaction ID: ${reactionId} (not found)`, id: reactionId };
    //         } else {
    //             throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    //         }
    //     } catch (error) {
    //         console.error(`Error fetching reaction ${reactionId}:`, error);
    //         return { name: `Reaction ID: ${reactionId}`, id: reactionId };
    //     }
    // };

    // Function to handle editing a query
    // const handleEditQuery = async (query) => {
    //     setViewMode('edit');
    //     setViewingQuery(null);
    //     setIsEditing(true);
    //     setEditingQueryId(query.id);
    //     setLoading(true);

    //     try {
    //         console.log('Original query data:', query);

    //         // Fetch drug names and reactions names by IDs
    //         const drugsToEdit = (query.drugs || []).map(d => ({
    //             id: d.id,
    //             name: d.name
    //         }));

    //         const reactionsToEdit = (query.reactions || []).map(r => ({
    //             id: r.id,
    //             name: r.name
    //         }));

    //         console.log('Drugs for editing (final):', drugsToEdit);
    //         console.log('Reactions for editing (final):', reactionsToEdit);

    //         const token = localStorage.getItem('token');
    //         if (!token) {
    //             alert('You are not logged in. Please log in first.');
    //             navigate('/');
    //             return;
    //         }

    //         const response = await axios.get(
    //             `http://127.0.0.1:8000/api/v1/analysis/queries/${query.id}/`,
    //             {
    //                 headers: {
    //                     'Authorization': `Bearer ${token}`
    //                 }
    //             }
    //         );

    //         setDrugs(drugsToEdit.length > 0 ? drugsToEdit : [{ name: '', id: null }]);
    //         setReactions(reactionsToEdit.length > 0 ? reactionsToEdit : [{ name: '', id: null }]);

    //         setYearStart(query.year_start ? query.year_start.toString() : '');
    //         setYearEnd(query.year_end ? query.year_end.toString() : '');
    //         setQuarterStart(query.quarter_start ? query.quarter_start.toString() : '');
    //         setQuarterEnd(query.quarter_end ? query.quarter_end.toString() : '');
    //         setQueryName(query.name || 'New Query');

    //         window.scrollTo({ top: 0, behavior: 'smooth' });
    //     } catch (error) {
    //         console.error('Error loading query for editing:', error);
    //         alert('Failed to load query data for editing');
    //         resetForm();
    //     } finally {
    //         setLoading(false);
    //     }
    // };


    const handleEditQuery = async (query) => {
        setViewMode('edit');
        setViewingQuery(null);
        setIsEditing(true);
        setEditingQueryId(query.id);
        setLoading(true);

        try {
            const token = localStorage.getItem('token');
            if (!token) {
                alert('You are not logged in. Please log in first.');
                navigate('/');
                return;
            }

            const response = await axios.get(
                `http://127.0.0.1:8000/api/v1/analysis/queries/${query.id}/`,
                {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                }
            );

            const queryData = response.data;

            console.log('Query data from backend:', queryData);

            const drugsToEdit = (queryData.drugs || []).map(d => ({
                id: d.id,
                name: d.name
            }));

            const reactionsToEdit = (queryData.reactions || []).map(r => ({
                id: r.id,
                name: r.name
            }));

            console.log('Drugs for editing (final):', drugsToEdit);
            console.log('Reactions for editing (final):', reactionsToEdit);

            setDrugs(drugsToEdit.length > 0 ? drugsToEdit : [{ name: '', id: null }]);
            setReactions(reactionsToEdit.length > 0 ? reactionsToEdit : [{ name: '', id: null }]);

            setYearStart(queryData.year_start ? queryData.year_start.toString() : '');
            setYearEnd(queryData.year_end ? queryData.year_end.toString() : '');
            setQuarterStart(queryData.quarter_start ? queryData.quarter_start.toString() : '');
            setQuarterEnd(queryData.quarter_end ? queryData.quarter_end.toString() : '');
            setQueryName(queryData.name || 'New Query');

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
    };

    const handleNewQuery = () => {
        setViewMode('new');
        setViewingQuery(null);
        resetForm();
    };

    const validateForm = () => {
        const validDrugs = drugs.filter(drug => drug.id !== null);
        const validReactions = reactions.filter(reaction => reaction.id !== null);

        // Check for required fields
        if (validDrugs.length === 0) {
            alert('Please select at least one valid drug from the search results.');
            return false;
        }

        if (validReactions.length === 0) {
            alert('Please select at least one valid reaction from the search results.');
            return false;
        }

        // בדיקה בטוחה לשדות - וידוא שהם לא undefined
        const safeYearStart = yearStart || '';
        const safeYearEnd = yearEnd || '';
        const safeQuarterStart = quarterStart || '';
        const safeQuarterEnd = quarterEnd || '';
        const safeQueryName = queryName || '';

        if (!safeYearStart.trim() || !safeYearEnd.trim() || !safeQuarterStart.trim() || !safeQuarterEnd.trim()) {
            alert('Please fill all year and quarter fields.');
            return false;
        }

        if (!safeQueryName.trim()) {
            alert('Please provide a name for your query.');
            return false;
        }

        // Enhanced year validation
        const startYear = parseInt(safeYearStart);
        const endYear = parseInt(safeYearEnd);
        const currentYear = new Date().getFullYear();

        if (isNaN(startYear) || isNaN(endYear)) {
            alert('Please enter valid year values.');
            return false;
        }

        if (startYear > endYear) {
            alert('Start year cannot be greater than end year');
            return false;
        }

        if (startYear < 1900 || endYear > currentYear + 10) {
            alert('Please enter realistic year values');
            return false;
        }

        // Quarter validation
        const startQuarter = parseInt(safeQuarterStart);
        const endQuarter = parseInt(safeQuarterEnd);

        if (isNaN(startQuarter) || isNaN(endQuarter)) {
            alert('Please enter valid quarter values.');
            return false;
        }

        if (startQuarter < 1 || startQuarter > 4 || endQuarter < 1 || endQuarter > 4) {
            alert('Quarters must be between 1 and 4.');
            return false;
        }

        // Additional validation: if same year, start quarter should not be after end quarter
        if (startYear === endYear && startQuarter > endQuarter) {
            alert('Start quarter cannot be after end quarter in the same year');
            return false;
        }

        return true;
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
                // if the request failed, show an error message
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

    return (
        <div className="user-profile-container">
            <div className="main-content">
                <div className="prompt-container">
                    {viewMode === 'view' && viewingQuery ? (
                        <QueryDetailsView query={viewingQuery} />
                    ) : (
                        <>
                            <div className="form-header">
                                <h2>{isEditing ? 'Update Query' : 'New Query'}</h2>
                                {isEditing && (
                                    <button
                                        type="button"
                                        className="cancel-button"
                                        onClick={cancelEditing}
                                    >
                                        Cancel
                                    </button>
                                )}

                                {showToast && (
                                    <div className="toast-notification">
                                        {toastMessage}
                                    </div>
                                )}
                            </div>

                            <form onSubmit={handleSubmitQuery}>
                                <div className="form-section">
                                    <div className="form-field">
                                        <div className="mb-2">
                                            <label className="block text-sm font-medium text-gray-700">Query Name</label>
                                            <input
                                                type="text"
                                                name="queryName"
                                                value={queryName}
                                                onChange={handleInputChange}
                                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                                                placeholder="Enter query name"
                                            />
                                        </div>

                                        <div className="mb-2">
                                            <label className="block text-sm font-medium text-gray-700">Start Year</label>
                                            <input
                                                type="number"
                                                min="1900"
                                                max="2100"
                                                name="startYear"
                                                value={yearStart}
                                                onChange={handleInputChange}
                                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                                            />
                                        </div>

                                        <div className="mb-2">
                                            <label className="block text-sm font-medium text-gray-700">End Year</label>
                                            <input
                                                type="number"
                                                min="1900"
                                                max="2100"
                                                name="endYear"
                                                value={yearEnd}
                                                onChange={handleInputChange}
                                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                                            />
                                        </div>

                                        <div className="mb-2">
                                            <label className="block text-sm font-medium text-gray-700">Start Quarter</label>
                                            <CustomSelect
                                                name="startQuarter"
                                                value={quarterStart}
                                                onChange={handleInputChange}
                                                placeholder="Select Quarter"
                                                options={[
                                                    { value: "1", label: "Quarter 1" },
                                                    { value: "2", label: "Quarter 2" },
                                                    { value: "3", label: "Quarter 3" },
                                                    { value: "4", label: "Quarter 4" }
                                                ]}
                                            />
                                        </div>

                                        <div className="mb-2">
                                            <label className="block text-sm font-medium text-gray-700">End Quarter</label>
                                            <CustomSelect
                                                name="endQuarter"
                                                value={quarterEnd}
                                                onChange={handleInputChange}
                                                placeholder="Select Quarter"
                                                options={[
                                                    { value: "1", label: "Quarter 1" },
                                                    { value: "2", label: "Quarter 2" },
                                                    { value: "3", label: "Quarter 3" },
                                                    { value: "4", label: "Quarter 4" }
                                                ]}
                                            />
                                        </div>
                                    </div>
                                    <h3 className="section-label">Drugs List</h3>
                                    {drugs.map((drug, index) => (
                                        <div key={`drug-${index}`} className="input-group">
                                            <input
                                                type="text"
                                                className="input-field"
                                                value={drug.name}
                                                onChange={(e) => handleDrugChange(index, e.target.value)}
                                                placeholder="Enter a drug..."
                                                dir="ltr"
                                            />
                                            {activeDrugSearchIndex === index && drugSearchResults.length > 0 && (
                                                <div className="search-results">
                                                    {drugSearchResults.map((result, resultIndex) => (
                                                        <div
                                                            key={resultIndex}
                                                            className="search-result-item"
                                                            onClick={() => selectDrug(result)}
                                                        >
                                                            {result.name}
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                            {(index > 0 || drugs.length > 1) && (
                                                <button
                                                    type="button"
                                                    className="remove-button"
                                                    onClick={() => removeDrugField(index)}
                                                >
                                                    <FaTimes />
                                                </button>
                                            )}
                                        </div>
                                    ))}
                                    <button
                                        type="button"
                                        className="add-button"
                                        onClick={addDrugField}
                                    >
                                        Add Drug <FaPlus />
                                    </button>
                                </div>

                                <div className="form-section">
                                    <h3 className="section-label">Reactions List</h3>
                                    {reactions.map((reaction, index) => (
                                        <div key={`reaction-${index}`} className="input-group">
                                            <input
                                                type="text"
                                                className="input-field"
                                                value={reaction.name}
                                                onChange={(e) => handleReactionChange(index, e.target.value)}
                                                placeholder="Enter a reaction..."
                                                dir="ltr"
                                            />
                                            {activeReactionSearchIndex === index && reactionSearchResults.length > 0 && (
                                                <div className="search-results">
                                                    {reactionSearchResults.map((result, resultIndex) => (
                                                        <div
                                                            key={resultIndex}
                                                            className="search-result-item"
                                                            onClick={() => selectReaction(result)}
                                                        >
                                                            {result.name}
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                            {(index > 0 || reactions.length > 1) && (
                                                <button
                                                    type="button"
                                                    className="remove-button"
                                                    onClick={() => removeReactionField(index)}
                                                >
                                                    <FaTimes />
                                                </button>
                                            )}
                                        </div>
                                    ))}
                                    <button
                                        type="button"
                                        className="add-button"
                                        onClick={addReactionField}
                                    >
                                        Add Reaction <FaPlus />
                                    </button>
                                </div>

                                <div className="submit-container">
                                    {submitError && (
                                        <div className="error-message" style={{ color: 'red', marginBottom: '10px' }}>
                                            {submitError}
                                        </div>
                                    )}
                                    <button
                                        type="submit"
                                        className="submit-button"
                                        disabled={
                                            isSubmitting ||
                                            drugs.every(d => !d.name || !d.name.trim()) ||
                                            reactions.every(r => !r.name || !r.name.trim())
                                        }
                                    >
                                        {isSubmitting ? (
                                            <>
                                                {isEditing ? 'Updating...' : 'Saving...'}
                                            </>
                                        ) : (
                                            <>
                                                {isEditing ? 'Update + Calc' : 'Save + Calc'}
                                            </>
                                        )}
                                    </button>
                                </div>
                            </form>
                        </>
                    )}
                </div>
            </div>

            <div className="sidebar">
                {showLogoutPopup && (
                    <div className="logout-popup">Logging out... You are being redirected.</div>
                )}
                <div className="logout-container">
                    <button className="logout-button" onClick={handleLogout} title="Logout">
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
                    {savedQueries.length === 0 ? (
                        <p className="no-queries">No Queries</p>
                    ) : (
                        <div className="queries-list">
                            {savedQueries.map((item) => (
                                <div key={item.id} className="query-card">
                                    <div className="query-item">
                                        <span className="query-name">{item.name}</span>
                                        <div className="query-actions">
                                            <button
                                                type="button"
                                                className="action-button view-button"
                                                onClick={() => handleViewQuery(item)}
                                                title="View Details"
                                            >
                                                <FaEye />
                                            </button>

                                            <button
                                                type="button"
                                                className="action-button edit-button"
                                                onClick={() => handleEditQuery(item)}
                                                title="Edit Query"
                                            >
                                                <FaEdit />
                                            </button>
                                            <button
                                                type="button"
                                                className="action-button delete-button"
                                                onClick={() => handleDeleteQuery(item.id)}
                                                title="Delete Query"
                                            >
                                                <FaTrash />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <div className="nav-buttons">
                    <button className="nav-button" onClick={handleNewQuery}>
                        <span>New Query</span>
                        <FaArrowRight />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default UserProfile;