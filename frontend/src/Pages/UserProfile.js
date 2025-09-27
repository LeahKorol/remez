import React, { useState, useEffect, useRef } from 'react';
import { FaUser, FaArrowRight, FaPlus, FaTimes, FaEdit, FaTrash, FaSignOutAlt, FaChevronDown, FaEye, FaFileCsv, FaFileImage, FaArrowDown, FaSearchPlus } from 'react-icons/fa';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { fetchWithRefresh } from '../utils/tokenService';
import CustomSelect from "../components/CustomSelect";
import QueryDetailsView from "../components/QueryDetailsView";
import { useUser } from "../utils/UserContext";
import { validateQueryForm } from '../utils/formValidation';
import Sidebar from '../components/Sidebar';
import ToastNotification from '../components/ToastNotification';
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

    const [viewMode, setViewMode] = useState('new');
    const [viewingQuery, setViewingQuery] = useState(null);

    const [showToast, setShowToast] = useState(false);
    const [toastMessage, setToastMessage] = useState('');

    const [zoomLevel, setZoomLevel] = useState(1);
    const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

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

                const userResponse = await fetchWithRefresh('http://127.0.0.1:8000/api/v1/auth/user/', {
                    method: 'GET'
                });

                if (!userResponse) {
                    // fetchWithRefresh handles redirect to login on auth failure
                    return;
                }

                console.log('User response status:', userResponse.status);

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


    const fetchQueries = async () => {
        try {
            const token = localStorage.getItem('token');

            if (!token) {
                console.log('No token for queries');
                return;
            }

            const response = await fetchWithRefresh('http://127.0.0.1:8000/api/v1/analysis/queries/', {
                method: 'GET'
            });

            if (!response) return;

            console.log('Queries response status:', response.status);

            if (response.ok) {
                const data = await response.json();
                console.log('Queries loaded:', data.length);

                console.log('📊 Raw data from server:', data);
                data.forEach((query, index) => {
                    console.log(`Query ${index + 1}:`, {
                        id: query.id,
                        name: query.name,
                        created: query.created_at,
                        hasRorValues: query.ror_values ? query.ror_values.length : 'NONE',
                        rorValues: query.ror_values,
                        hasRorLower: !!query.ror_lower,
                        hasRorUpper: !!query.ror_upper
                    });
                });

                // Sort queries: those with results first, then by creation date descending
                const sortedQueries = data.sort((a, b) => {
                    const aHasResults = a.ror_values && a.ror_values.length > 0;
                    const bHasResults = b.ror_values && b.ror_values.length > 0;

                    if (aHasResults && !bHasResults) return -1;
                    if (!aHasResults && bHasResults) return 1;

                    // if both have or both don't have results, sort by creation date descending
                    return new Date(b.created_at) - new Date(a.created_at);
                });

                setSavedQueries(sortedQueries);
            } else {
                console.error('Failed to fetch queries:', response.status);
            }
        } catch (error) {
            console.error('Error fetching queries:', error);
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

    const showToastMessage = (message) => {
        setToastMessage(message);
        setShowToast(true);
        setTimeout(() => setShowToast(false), 3000);
    };


    // Handle form submission for saving or updating queries
    const handleSubmitQuery = async (e) => {
        e.preventDefault();
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
                reactions: reactions.filter(r => r.id).map(r => r.id),
                user_id: userId
            };

            console.log('Submitting payload:', payload);

            const submitButton = e.target.querySelector('button[type="submit"]');
            submitButton.innerHTML = '<div class="spinner-small"></div> Processing...';

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
            console.log('Received query with ID:', newQuery.id);

            if (editingQueryId) {
                setSavedQueries(savedQueries.map(q => q.id === newQuery.id ? newQuery : q));
                showToastMessage('Query updated successfully!');
            } else {
                setSavedQueries([newQuery, ...savedQueries]);
                showToastMessage('Query saved successfully!');
            }

            resetForm();

            // redirect to loading page with query data
            navigate('/loading', {
                state: {
                    queryData: {
                        ...newQuery,
                        userId: userId,
                        userEmail: user?.email,
                        // Include the actual drug and reaction names for display
                        displayDrugs: drugs.filter(d => d.id).map(d => ({ name: d.name })),
                        displayReactions: reactions.filter(r => r.id).map(r => ({ name: r.name }))
                    },
                    isUpdate: !!editingQueryId
                }
            });

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
            setGlobalLoading(false);
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


    // Add useEffect to handle success messages from loading page
    useEffect(() => {
        // Check for success message from loading page
        const state = location.state;
        if (state?.message && state?.type === 'success') {
            showToastMessage(state.message);

            // Clear the state to prevent re-showing on refresh
            window.history.replaceState({}, document.title);
        }
    }, [location.state]);


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

            const response = await fetchWithRefresh(`http://127.0.0.1:8000/api/v1/analysis/queries/${queryId}/`, {
                method: 'DELETE'
            });

            if (!response) {
                // fetchWithRefresh handles redirect to login on auth failure
                return;
            }

            console.log('Delete response status:', response.status);

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

            const response = await fetchWithRefresh(`http://127.0.0.1:8000/api/v1/analysis/queries/${query.id}/`);

            if (!response) {
                alert('Failed to load query data for editing');
                resetForm();
                return;
            }

            const queryData = await response.json();


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

    return (
        <div className="user-profile-container">
            <div className="main-content">
                <div className="prompt-container">
                    {viewMode === 'view' && viewingQuery ? (
                        <QueryDetailsView query={viewingQuery} handleNewQuery={handleNewQuery} />
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

                                <ToastNotification message={toastMessage} type="error" />

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
                                                onChange={(e) => {
                                                    setQueryName(e.target.value);

                                                    // validate on the fly
                                                    const errors = validateQueryForm({
                                                        drugs,
                                                        reactions,
                                                        yearStart,
                                                        yearEnd,
                                                        quarterStart,
                                                        quarterEnd,
                                                        queryName: e.target.value
                                                    });

                                                    if (errors.length > 0) {
                                                        errors.forEach(err => showToastMessage(err));
                                                    }
                                                }}
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

            <Sidebar
                user={user}
                savedQueries={savedQueries}
                onViewQuery={handleViewQuery}
                onEditQuery={handleEditQuery}
                onDeleteQuery={handleDeleteQuery}
                onNewQuery={handleNewQuery}
                showLogoutConfirm={showLogoutConfirm}
                showLogoutPopup={showLogoutPopup}
                handleLogoutClick={setShowLogoutConfirm}
                handleLogout={handleLogout}
            />
        </div>
    );
};

export default UserProfile;