import React, { useState, useEffect, useRef } from 'react';
import { FaUser, FaArrowRight, FaPlus, FaTimes, FaEdit, FaTrash, FaSignOutAlt, FaSearch } from 'react-icons/fa';
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

  // fetch user data on component mount
  useEffect(() => {
    const fetchUserData = async () => {
      try {
        setLoading(true);

        const token = localStorage.getItem('token');
        console.log('token:', token);

        if (!token) {
          throw new Error('No authentication token found');
        }

        const userResponse = await fetch('http://127.0.0.1:8000/api/v1/auth/user/', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!userResponse.ok) {
          throw new Error('Failed to fetch user data');
        }

        const userData = await userResponse.json();
        const userName = userData.email.split('@')[0];
        setUser({ ...userData, name: userName });


        fetchQueries();

      } catch (error) {
        console.error('Error fetching user data:', error);
        setError('An error occurred while loading user data');
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
      const response = await fetch('http://127.0.0.1:8000/api/v1/analysis/queries/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSavedQueries(data);
      }
      else {
        throw new Error('Failed to fetch queries');
      }
    }
    catch (error) {
      console.error('Error fetching queries:', error);
      setError('An error occurred while loading queries');
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
      const response = await fetch(`http://127.0.0.1:8000/api/v1/analysis/drug-names/seach/${prefix}/`, {
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


  // Get CSRF token from cookies
  const getCSRFToken = () => {
    const cookies = document.cookie.split('; ');
    const csrfCookie = cookies.find(cookie => cookie.startsWith('csrftoken='));
    return csrfCookie ? csrfCookie.split('=')[1] : null;
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

    const csrfToken = getCSRFToken();  // get this token from cookies
    const token = localStorage.getItem('token');

    if (!token || !csrfToken) {
      alert('You are not logged in. Please log in first.');
      return;
    }

    const data = {
      name: queryName,
      drug_ids: validDrugs.map(drug => drug.id),
      reaction_ids: validReactions.map(reaction => reaction.id),
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

      const response = await fetch(url, {
        method: method,
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          'X-CSRFTOKEN': csrfToken,
        },
        body: JSON.stringify(data),
      });

      if (response.ok) {
        const newQuery = await response.json();
        setSavedQueries([newQuery, ...savedQueries]);
        setDrugs(['']);
        setReactions(['']);
      } else {
        const error = await response.json();
        console.error('Error saving query : ', error);
        alert('Failed to save query : ', error.massage || 'unknown error');
      }
    } catch (error) {
      console.error('Error saving query:', error);
      alert('An error occurred while saving the query : ', error.message || 'unknown error');
    }
  };


  const handleEditQueryName = (queryId, newName) => {
    const updatedQueries = savedQueries.map(query => {
      if (query.id === queryId) {
        return { ...query, name: newName };
      }
      return query;
    });
    setSavedQueries(updatedQueries);
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
  };

  const addReactionField = () => {
    setReactions([...reactions, '']);
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
    setDrugs([...query.drugs, '']);
    setReactions([...query.reactions, '']);

    // add scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleDeleteQuery = (queryId) => {
    if (window.confirm('Are you sure you want to delete this query?')) {
      // מבצעים מחיקה מהדאטה-בייס
      // const { error } = await supabase.from('queries').delete().eq('id', queryId);

      // local deleting
      setSavedQueries(savedQueries.filter(query => query.id !== queryId));
    }
  };

  const cancelEditing = () => {
    setIsEditing(false);
    setEditingQueryId(null);
    setDrugs(['']);
    setReactions(['']);
  };

  const handleNewQuery = () => {
    setDrugs(['']);  // reset drugs list
    setReactions(['']);  // reset reactions list
  };


  const handleLogout = async () => {
    setShowLogoutPopup(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/auth/logout/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        localStorage.removeItem('token');  // remove the token from local storage
        setShowLogoutPopup(false);
        navigate('/');  // go to home page
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
                cancel
              </button>
            )}
          </div>

          <form onSubmit={handleSubmitQuery}>
            <div className="form-section">
              <h3 className="section-label">Drugs list</h3>
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
                add drug <FaPlus />
              </button>
            </div>


            <div className="form-section">
              <h3 className="section-label">Reactions list</h3>
              {reactions.map((reaction, index) => (
                <div key={`effect-${index}`} className="input-group">
                  <input
                    type="text"
                    className="input-field"
                    value={reaction.name}
                    onChange={(e) => handleReactionChange(index, e.target.value)}
                    placeholder="Enter a reaction..."
                    dir="ltr"
                  />
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
                add reaction <FaPlus />
              </button>
            </div>

            <div className="submit-container">
              <button
                type="submit"
                className="submit-button"
                disabled={!drugs[0]?.name?.trim() || !reactions[0]?.name?.trim()}
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
                  <div className="query-header">
                    <span className="query-date">
                      {new Date(item.created_at).toLocaleDateString('he-IL')}
                    </span>

                    <div className="query-actions">
                      <button
                        type="button"
                        className="action-button edit-button"
                        onClick={() => {
                          const newName = prompt('Enter new name for the query:', item.name);
                          if (newName) {
                            handleEditQueryName(item.id, newName);
                          }
                        }}
                        title="Edit Query Name"
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
                  <div className="query-content">
                    <div className="query-name">
                      <strong>Query Name:</strong> {item.name}
                    </div>
                    <div className="query-drugs">
                      <strong>Drugs:</strong> {item.drugs.join(', ')}
                    </div>
                    <div className="query-reactions">
                      <strong>Reaction:</strong> {item.reactions.join(', ')}
                    </div>
                    <div className="result-divider"></div>
                    <p className="query-result">{item.result}</p>
                    {item.updated_at && (
                      <div className="updated-note">
                        Updated: {new Date(item.updated_at).toLocaleDateString('he-IL')}
                      </div>
                    )}
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