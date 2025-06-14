import React, { useState, useEffect, useRef } from 'react';
import { FaUser, FaArrowRight, FaPlus, FaTimes, FaEdit, FaTrash, FaSignOutAlt, FaChevronDown, FaChevronRight } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import { fetchWithRefresh } from './Login';
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
                
                const userName = userData.email ? userData.email.split('@')[0] : 'User';
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
        newDrugs[index] = { name: value, id: null }; // Reset ID when changing name
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

    // Get CSRF token from cookies
    const getCSRFToken = () => {
        const cookies = document.cookie.split('; ');
        const csrfCookie = cookies.find(cookie => cookie.startsWith('csrftoken='));
        return csrfCookie ? csrfCookie.split('=')[1] : null;
    };

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

    const handleSubmitQuery = async (e) => {
        e.preventDefault();
    
        const validDrugs = drugs.filter(drug => drug.id !== null);
        const validReactions = reactions.filter(reaction => reaction.id !== null);
    
        // Validate form inputs
        if (validDrugs.length === 0) {
            alert('Please select at least one valid drug from the search results.');
            return;
        }
    
        if (validReactions.length === 0) {
            alert('Please select at least one valid reaction from the search results.');
            return;
        }
    
        if (!yearStart || !yearEnd || !quarterStart || !quarterEnd) {
            alert('Please fill all year and quarter fields.');
            return;
        }
    
        if (!queryName.trim()) {
            alert('Please provide a name for your query.');
            return;
        }
    
        if (parseInt(yearStart) > parseInt(yearEnd)) {
            alert('Start year cannot be greater than end year');
            return;
        }
        if (parseInt(quarterStart) > 4 || parseInt(quarterStart) < 1 || parseInt(quarterEnd) < 1 || parseInt(quarterEnd) > 4) {
            alert('Not a valid quarter. Quarters must be between 1 and 4.');
            return;
        }
    
        // Fixed data structure to match API schema
        const data = {
            name: queryName,
            drugs: validDrugs.map(drug => drug.id),
            reactions: validReactions.map(reaction => reaction.id),
            year_start: parseInt(yearStart),
            year_end: parseInt(yearEnd),
            quarter_start: parseInt(quarterStart),
            quarter_end: parseInt(quarterEnd),
        };
    
        try {
            // Determine if we're creating or updating a query
            const url = isEditing
                ? `http://127.0.0.1:8000/api/v1/analysis/queries/${editingQueryId}/`
                : 'http://127.0.0.1:8000/api/v1/analysis/queries/';
    
            const method = isEditing ? 'PUT' : 'POST';
    
            // Get token and use regular fetch with proper headers
            const token = localStorage.getItem('token');
            
            if (!token) {
                alert('You are not logged in. Please log in first.');
                return;
            }
    
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify(data),
            });
    
            if (response.ok) {
                const newQuery = await response.json();
                if (isEditing) {
                    setSavedQueries(savedQueries.map(q => q.id === newQuery.id ? newQuery : q));
                } else {
                    setSavedQueries([newQuery, ...savedQueries]);
                }
                resetForm();
                alert('Query saved successfully!');
            } else {
                const errorText = await response.text();
                let errorMessage = 'Unknown error';
                
                try {
                    const errorJson = JSON.parse(errorText);
                    errorMessage = errorJson.message || errorJson.detail || 'Unknown error';
                } catch {
                    errorMessage = errorText || 'Unknown error';
                }
                
                console.error('Error saving query:', errorMessage);
                alert(`Failed to save query: ${errorMessage}`);
            }
        } catch (error) {
            console.error('Error saving query:', error);
            alert(`Failed to save query: ${error.message || 'unknown error'}`);
        }
    };

    const handleDeleteQuery = async (queryId) => {
        if (!window.confirm('Are you sure you want to delete this query?')) {
            return;
        }
    
        try {
            const response = await fetchWithRefresh(`http://127.0.0.1:8000/api/v1/analysis/queries/${queryId}/`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
    
            if (response.ok) {
                setSavedQueries(savedQueries.filter(q => q.id !== queryId));
            } else {
                throw new Error('Failed to delete query');
            }
        } catch (error) {
            console.error('Error deleting query:', error);
            alert('Failed to delete query');
        }
    };

    const handleEditQueryName = async (queryId, newName) => {
        try {
            const response = await fetchWithRefresh(`http://127.0.0.1:8000/api/v1/analysis/queries/${queryId}/`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: newName })
            });
    
            if (response.ok) {
                const updatedQuery = await response.json();
                setSavedQueries(savedQueries.map(query =>
                    query.id === queryId ? { ...query, name: newName } : query
                ));
            } else {
                alert('Failed to update query name');
            }
        } catch (error) {
            console.error('Error updating query name:', error);
            alert('Failed to update query name');
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
        newReactions[index] = { name: value, id: null };
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

    // update & delete queries
    const handleEditQuery = (query) => {
        setIsEditing(true);
        setEditingQueryId(query.id);
        setDrugs(query.drugs.map(d => ({ name: d.name || d, id: d.id || null })).concat({ name: '', id: null }));
        setReactions(query.reactions.map(r => ({ name: r.name || r, id: r.id || null })).concat({ name: '', id: null }));
        setYearStart(query.year_start?.toString() || '');
        setYearEnd(query.year_end?.toString() || '');
        setQuarterStart(query.quarter_start?.toString() || '');
        setQuarterEnd(query.quarter_end?.toString() || '');
        setQueryName(query.name || 'New Query');

        // add scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };    

    const cancelEditing = () => {
        resetForm();
    };

    const handleNewQuery = () => {
        resetForm();
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
                            <button
                                type="submit"
                                className="submit-button"
                                disabled={
                                    drugs.every(d => !d.name.trim()) ||
                                    reactions.every(r => !r.name.trim())
                                }
                            >
                                {isEditing ? 'Update + Calc' : 'Save + Calc'}
                            </button>
                        </div>
                    </form>
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