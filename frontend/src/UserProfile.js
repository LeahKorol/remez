import React, { useState, useEffect } from 'react';
import { FaUser, FaArrowRight, FaPlus, FaTimes, FaEdit, FaTrash, FaSignOutAlt } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import './UserProfile.css';


const UserProfile = () => {
  const [drugs, setdrugs] = useState(['']);
  const [reactions, setReactions] = useState(['']);
  const [yearStart, setYearStart] = useState('');
  const [yearEnd, setYearEnd] = useState('');
  const [quarterStart, setQuarterStart] = useState('');
  const [quarterEnd, setQuarterEnd] = useState('');
  const [user, setUser] = useState(null);
  const [savedQueries, setSavedQueries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [queryName, setQueryName] = useState('');
  const [editingQueryId, setEditingQueryId] = useState(null);
  const [showLogoutPopup, setShowLogoutPopup] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        setLoading(true);

        const token = localStorage.getItem('token');
        console.log('token:', token);

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


  const getCSRFToken = () => {
    const cookies = document.cookie.split('; ');
    const csrfCookie = cookies.find(cookie => cookie.startsWith('csrftoken='));
    return csrfCookie ? csrfCookie.split('=')[1] : null;
  };


  const handleSubmitQuery = async (e) => {
    e.preventDefault();

    const validdrugs = drugs.filter(med => med.trim() !== '');
    const validReactions = reactions.filter(effect => effect.trim() !== '');

    if (!validdrugs.length || !validReactions.length || !user) {
      alert('Please enter at least one drug and one side reaction.');
      return;
    }

    const csrfToken = getCSRFToken();  // get this token from cookies
    const token = localStorage.getItem('token');

    if (!token || !csrfToken) {
      alert('You are not logged in. Please log in first.');
      return;
    }

    const data = {
      name: queryName || 'New Query',
      drugs: validdrugs,
      reactions: validReactions,
      year_start: parseInt(yearStart),
      year_end: parseInt(yearEnd),
      quarter_start: parseInt(quarterStart),
      quarter_end: parseInt(quarterEnd),
    };

    if (!yearStart || !yearEnd || !quarterStart || !quarterEnd) {
      alert('Please fill all year and quarter fields.');
      return;
    }

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/analysis/queries/', {
        method: 'POST',
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
        setdrugs(['']);
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


  // drugs management functions
  const handleDrugChange = (index, value) => {
    const newdrugs = [...drugs];
    newdrugs[index] = value;
    setdrugs(newdrugs);
  };

  const addDrugField = () => {
    setdrugs([...drugs, '']);
  };

  const removeDrugField = (index) => {
    if (drugs.length > 1) {
      const newdrugs = [...drugs];
      newdrugs.splice(index, 1);
      setdrugs(newdrugs);
    }
  };

  // reactions management functions
  const handleReactionChange = (index, value) => {
    const newReactions = [...reactions];
    newReactions[index] = value;
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
    setdrugs([...query.drugs, '']);
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
    setdrugs(['']);
    setReactions(['']);
  };

  const handleNewQuery = () => {
    setdrugs(['']);  // reset drugs list
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
                    value={drug}
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
                    value={reaction}
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
                disabled={!drugs[0]?.trim() || !reactions[0]?.trim()}
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