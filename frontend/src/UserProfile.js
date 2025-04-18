// import React, { useState, useEffect } from 'react';
// import { FaUser, FaArrowRight } from 'react-icons/fa';
// import { createClient } from '@supabase/supabase-js';
// import './UserProfile.css';

// // const supabaseUrl = 'https://your-supabase-url.supabase.co';
// // const supabaseKey = 'your-supabase-key';
// // const supabase = createClient(supabaseUrl, supabaseKey);

// const UserProfile = () => {
//   const [prompt, setPrompt] = useState('');
//   const [user, setUser] = useState(null);
//   const [savedQueries, setSavedQueries] = useState([]);
//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState(null);

//   useEffect(() => {
//     // השורות של Supabase נשמרות, אבל במקומן משתמשים בנתונים מדומים
//     const fetchUserData = async () => {
//       try {
//         setLoading(true);

//         // במקום לקבל משתמש מ-Supabase, משתמשים בנתונים מדומים
//         // עדיין שומרים את הקוד המקורי בהערות
//         /*
//         const { data: { user } } = await supabase.auth.getUser();

//         if (user) {
//           const { data: profileData, error: profileError } = await supabase
//             .from('profiles')
//             .select('*')
//             .eq('id', user.id)
//             .single();

//           if (profileError) throw profileError;

//           const { data: queries, error: queriesError } = await supabase
//             .from('queries')
//             .select('*')
//             .eq('user_id', user.id)
//             .order('created_at', { ascending: false });

//           if (queriesError) throw queriesError;

//           setSavedQueries(queries || []);
//         }
//         */

//         // נתונים מדומים למשתמש
//         const mockUser = {
//           id: 'user-123',
//           email: 'user@remez.com',
//           name: 'Remez User',
//         };

//         // נתונים מדומים לשאילתות
//         const mockQueries = [
//           {
//             id: 1,
//             user_id: 'user-123',
//             query: 'כמה עולה ביטוח לרכב לנהג חדש?',
//             result: 'ביטוח לרכב לנהג חדש עולה בין 5,000 ל-10,000 ש״ח בשנה, תלוי בגיל, מין, וסוג הרכב.',
//             created_at: '2025-03-28T14:30:00Z'
//           },
//           {
//             id: 2,
//             user_id: 'user-123',
//             query: 'מה ההבדל בין ביטוח מקיף לביטוח צד ג׳?',
//             result: 'ביטוח מקיף כולל כיסוי לנזקי הרכב שלך בנוסף לנזקים שגרמת לרכב אחר, בעוד ביטוח צד ג׳ מכסה רק נזקים שגרמת לרכב אחר.',
//             created_at: '2025-03-25T10:15:00Z'
//           },
//           {
//             id: 3,
//             user_id: 'user-123',
//             query: 'האם ביטוח חובה מכסה תאונות בחו״ל?',
//             result: 'לא, ביטוח חובה מכסה רק תאונות בתחומי מדינת ישראל והשטחים. לנסיעות לחו״ל יש לרכוש ביטוח נפרד.',
//             created_at: '2025-03-20T08:45:00Z'
//           }
//         ];

//         setUser(mockUser);
//         setSavedQueries(mockQueries);

//       } catch (error) {
//         console.error('Error fetching user data:', error);
//         setError('אירעה שגיאה בטעינת נתוני המשתמש');
//       } finally {
//         // מדמים עיכוב קצר כדי להראות את מצב הטעינה
//         setTimeout(() => {
//           setLoading(false);
//         }, 1500);
//       }
//     };

//     fetchUserData();
//   }, []);

//   const handleSubmit = async (e) => {
//     e.preventDefault();
//     if (!prompt.trim() || !user) return;

//     try {
//       const result = "תוצאה לדוגמה - כאן תהיה התשובה האמיתית מהשרת";

//       // שומרים את הקוד המקורי בהערות
//       /*
//       const { data, error } = await supabase
//         .from('queries')
//         .insert([
//           {
//             user_id: user.id,
//             query: prompt,
//             result: result,
//           }
//         ])
//         .select();

//       if (error) throw error;
//       */

//       // במקום להכניס לדאטה-בייס, פשוט מוסיפים לסטייט המקומי
//       const newQuery = {
//         id: Date.now(), // משתמשים בזמן נוכחי כמזהה ייחודי
//         user_id: user.id,
//         query: prompt,
//         result: result,
//         created_at: new Date().toISOString()
//       };

//       setSavedQueries([newQuery, ...savedQueries]);
//       setPrompt('');

//     } catch (error) {
//       console.error('Error saving query:', error);
//       alert('אירעה שגיאה בשמירת השאילתה');
//     }
//   };

//   if (loading) {
//     return <div className="loading">Loading...</div>;
//   }

//   if (error) {
//     return <div className="error">{error}</div>;
//   }

//   if (!user) {
//     return <div className="not-logged-in">Login for watching your profile</div>;
//   }

//   return (
//     <div className="user-profile-container">
//       <div className="main-content">
//         <div className="prompt-container">
//           <form onSubmit={handleSubmit}>
//             <div className="prompt-input-wrap">
//               <button type="submit" className="submit-button" disabled={!prompt.trim()}>
//                 send + calc
//               </button>
//               <input
//                 type="text"
//                 className="prompt-input"
//                 value={prompt}
//                 onChange={(e) => setPrompt(e.target.value)}
//                 placeholder="Enter your Query here..."
//                 dir="ltr"
//               />

//             </div>
//           </form>
//         </div>
//       </div>

//       <div className="sidebar">
//         <div className="user-info">
//           <div className="avatar-circle">
//             <FaUser className="user-icon" />
//           </div>
//           <h3 className="user-name">{user.name}</h3>
//           <p className="user-email">{user.email}</p>
//         </div>

//         <div className="saved-queries-section">
//           <h2 className="section-title">Your Queries</h2>
//           {savedQueries.length === 0 ? (
//             <p className="no-queries">No Queries</p>
//           ) : (
//             <div className="queries-list">
//               {savedQueries.map((item) => (
//                 <div key={item.id} className="query-card">
//                   <div className="query-header">
//                     <h3 className="query-text">{item.query}</h3>
//                     <span className="query-date">
//                       {new Date(item.created_at).toLocaleDateString('he-IL')}
//                     </span>
//                   </div>
//                   <p className="query-result">{item.result}</p>
//                 </div>
//               ))}
//             </div>
//           )}
//         </div>

//         <div className="nav-buttons">
//           <button className="nav-button">
//             <span>another page</span>
//             <FaArrowRight />
//           </button>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default UserProfile;


// import React, { useState, useEffect } from 'react';
// import { FaUser, FaArrowRight, FaPlus, FaTimes } from 'react-icons/fa';
// import { createClient } from '@supabase/supabase-js';
// import './UserProfile.css';

// // const supabaseUrl = 'https://your-supabase-url.supabase.co';
// // const supabaseKey = 'your-supabase-key';
// // const supabase = createClient(supabaseUrl, supabaseKey);

// const UserProfile = () => {
//   const [drugs, setdrugs] = useState(['']);
//   const [reactions, setreactions] = useState(['']);
//   const [user, setUser] = useState(null);
//   const [savedQueries, setSavedQueries] = useState([]);
//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState(null);

//   useEffect(() => {
//     // השורות של Supabase נשמרות, אבל במקומן משתמשים בנתונים מדומים
//     const fetchUserData = async () => {
//       try {
//         setLoading(true);

//         // נתונים מדומים למשתמש
//         const mockUser = {
//           id: 'user-123',
//           email: 'example@email.com',
//           name: 'ישראל ישראלי',
//         };

//         // נתונים מדומים לשאילתות - עם מבנה חדש המתאים לתרופות ותופעות לוואי
//         const mockQueries = [
//           {
//             id: 1,
//             user_id: 'user-123',
//             drugs: ['אומפרזול', 'סימבסטטין', 'אספירין'],
//             reactions: ['כאב ראש', 'עייפות', 'בחילה'],
//             result: 'קיימת התאמה בין תופעת הלוואי "כאב ראש" לתרופה "אספירין". מומלץ להתייעץ עם רופא.',
//             created_at: '2025-03-28T14:30:00Z'
//           },
//           {
//             id: 2,
//             user_id: 'user-123',
//             drugs: ['אמוקסיצילין', 'לבופלוקסצין'],
//             reactions: ['פריחה בעור', 'סחרחורת'],
//             result: 'נמצאה התאמה בין "פריחה בעור" לתרופה "אמוקסיצילין". זוהי תופעת לוואי ידועה שמופיעה ב-3% מהמטופלים.',
//             created_at: '2025-03-25T10:15:00Z'
//           }
//         ];

//         setUser(mockUser);
//         setSavedQueries(mockQueries);

//       } catch (error) {
//         console.error('Error fetching user data:', error);
//         setError('אירעה שגיאה בטעינת נתוני המשתמש');
//       } finally {
//         // מדמים עיכוב קצר כדי להראות את מצב הטעינה
//         setTimeout(() => {
//           setLoading(false);
//         }, 500);
//       }
//     };

//     fetchUserData();
//   }, []);

//   // פונקציות לניהול שדות התרופות
//   const handledrugChange = (index, value) => {
//     const newdrugs = [...drugs];
//     newdrugs[index] = value;
//     setdrugs(newdrugs);
//   };

//   const adddrugField = () => {
//     setdrugs([...drugs, '']);
//   };

//   const removedrugField = (index) => {
//     if (drugs.length > 1) {
//       const newdrugs = [...drugs];
//       newdrugs.splice(index, 1);
//       setdrugs(newdrugs);
//     }
//   };

//   // פונקציות לניהול שדות תופעות הלוואי
//   const handlereactionChange = (index, value) => {
//     const newreactions = [...reactions];
//     newreactions[index] = value;
//     setreactions(newreactions);
//   };

//   const addreactionField = () => {
//     setreactions([...reactions, '']);
//   };

//   const removereactionField = (index) => {
//     if (reactions.length > 1) {
//       const newreactions = [...reactions];
//       newreactions.splice(index, 1);
//       setreactions(newreactions);
//     }
//   };

//   const handleSubmit = async (e) => {
//     e.preventDefault();

//     // בדיקה שהוזנו נתונים תקינים
//     const validdrugs = drugs.filter(med => med.trim() !== '');
//     const validreactions = reactions.filter(effect => effect.trim() !== '');

//     if (!validdrugs.length || !validreactions.length || !user) {
//       alert('נא להזין לפחות תרופה אחת ותופעת לוואי אחת');
//       return;
//     }

//     try {
//       // במציאות, כאן נשלח בקשה לשרת שיעבד את הנתונים
//       const result = "תוצאה לדוגמה - ניתוח הקשר בין התרופות לתופעות הלוואי";

//       // במקום להכניס לדאטה-בייס, פשוט מוסיפים לסטייט המקומי
//       const newQuery = {
//         id: Date.now(),
//         user_id: user.id,
//         drugs: validdrugs,
//         reactions: validreactions,
//         result: result,
//         created_at: new Date().toISOString()
//       };

//       setSavedQueries([newQuery, ...savedQueries]);

//       // איפוס השדות לאחר שליחה
//       setdrugs(['']);
//       setreactions(['']);

//     } catch (error) {
//       console.error('Error saving query:', error);
//       alert('אירעה שגיאה בשמירת השאילתה');
//     }
//   };

//   if (loading) {
//     return <div className="loading">טוען...</div>;
//   }

//   if (error) {
//     return <div className="error">{error}</div>;
//   }

//   if (!user) {
//     return <div className="not-logged-in">התחבר כדי לצפות בפרופיל שלך</div>;
//   }

//   return (
//     <div className="user-profile-container">
//       <div className="main-content">
//         <div className="prompt-container">
//           <form onSubmit={handleSubmit}>
//             <div className="form-section">
//               <h3 className="section-label">רשימת תרופות</h3>
//               {drugs.map((drug, index) => (
//                 <div key={`med-${index}`} className="input-group">
//                   <input
//                     type="text"
//                     className="input-field"
//                     value={drug}
//                     onChange={(e) => handledrugChange(index, e.target.value)}
//                     placeholder="הזן שם תרופה"
//                     dir="ltr"
//                   />
//                   {index > 0 && (
//                     <button
//                       type="button"
//                       className="remove-button"
//                       onClick={() => removedrugField(index)}
//                     >
//                       <FaTimes />
//                     </button>
//                   )}
//                 </div>
//               ))}
//               <button
//                 type="button"
//                 className="add-button"
//                 onClick={adddrugField}
//               >
//                 <FaPlus /> הוסף תרופה
//               </button>
//             </div>

//             <div className="form-section">
//               <h3 className="section-label">רשימת תופעות לוואי</h3>
//               {reactions.map((reaction, index) => (
//                 <div key={`effect-${index}`} className="input-group">
//                   <input
//                     type="text"
//                     className="input-field"
//                     value={reaction}
//                     onChange={(e) => handlereactionChange(index, e.target.value)}
//                     placeholder="הזן תופעת לוואי"
//                     dir="ltr"
//                   />
//                   {index > 0 && (
//                     <button
//                       type="button"
//                       className="remove-button"
//                       onClick={() => removereactionField(index)}
//                     >
//                       <FaTimes />
//                     </button>
//                   )}
//                 </div>
//               ))}
//               <button
//                 type="button"
//                 className="add-button"
//                 onClick={addreactionField}
//               >
//                 <FaPlus /> הוסף תופעת לוואי
//               </button>
//             </div>

//             <div className="submit-container">
//               <button
//                 type="submit"
//                 className="submit-button"
//                 disabled={!drugs[0].trim() || !reactions[0].trim()}
//               >
//                 בדוק קשר בין תרופות לתופעות לוואי
//               </button>
//             </div>
//           </form>
//         </div>
//       </div>

//       <div className="sidebar">
//         <div className="user-info">
//           <div className="avatar-circle">
//             <FaUser className="user-icon" />
//           </div>
//           <h3 className="user-name">{user.name}</h3>
//           <p className="user-email">{user.email}</p>
//         </div>

//         <div className="saved-queries-section">
//           <h2 className="section-title">הבדיקות שלך</h2>
//           {savedQueries.length === 0 ? (
//             <p className="no-queries">אין בדיקות</p>
//           ) : (
//             <div className="queries-list">
//               {savedQueries.map((item) => (
//                 <div key={item.id} className="query-card">
//                   <div className="query-header">
//                     <span className="query-date">
//                       {new Date(item.created_at).toLocaleDateString('he-IL')}
//                     </span>
//                   </div>
//                   <div className="query-content">
//                     <div className="query-drugs">
//                       <strong>תרופות:</strong> {item.drugs.join(', ')}
//                     </div>
//                     <div className="query-side-effects">
//                       <strong>תופעות לוואי:</strong> {item.reactions.join(', ')}
//                     </div>
//                     <div className="result-divider"></div>
//                     <p className="query-result">{item.result}</p>
//                   </div>
//                 </div>
//               ))}
//             </div>
//           )}
//         </div>

//         <div className="nav-buttons">
//           <button className="nav-button">
//             <span>עמוד נוסף</span>
//             <FaArrowRight />
//           </button>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default UserProfile;



import React, { useState, useEffect } from 'react';
import { FaUser, FaArrowRight, FaPlus, FaTimes, FaEdit, FaTrash, FaSignOutAlt } from 'react-icons/fa';
import { createClient } from '@supabase/supabase-js';
import { useNavigate } from 'react-router-dom';
import './UserProfile.css';

// const supabaseUrl = 'https://your-supabase-url.supabase.co';
// const supabaseKey = 'your-supabase-key';
// const supabase = createClient(supabaseUrl, supabaseKey);

const UserProfile = () => {
  const [drugs, setdrugs] = useState(['']);
  const [reactions, setReactions] = useState(['']);
  const [user, setUser] = useState(null);
  const [savedQueries, setSavedQueries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editingQueryId, setEditingQueryId] = useState(null);
  const [showLogoutPopup, setShowLogoutPopup] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        setLoading(true);

        const mockUser = {
          id: 'user-123',
          email: 'john.doe@remez.com',
          name: 'John Doe',
        };

        // in this level we use fake data. In real life we would fetch data from the supabase
        const mockQueries = [
          {
            id: 1,
            user_id: 'user-123',
            drugs: ['omeprazole', 'simvastatin', 'aspirin'],
            reactions: ['headache', 'fatigue', 'nausea'],
            result: 'There is a match between the side effect "headache" and the drug "aspirin". It is recommended to consult a doctor.',
            created_at: '2025-03-28T14:30:00Z'
          },
          {
            id: 2,
            user_id: 'user-123',
            drugs: ['amoxicillin', 'levofloxacin'],
            reactions: ['skin rash', 'dizziness'],
            result: 'A match was found between "skin rash" and the drug "amoxicillin". This is a known side effect that occurs in 3% of patients.',
            created_at: '2025-03-25T10:15:00Z'
          }
        ];

        setUser(mockUser);
        setSavedQueries(mockQueries);

      } catch (error) {
        console.error('Error fetching user data:', error);
        setError('An error occurred while loading user data');
      } finally {
        // delay to show loading state
        setTimeout(() => {
          setLoading(false);
        }, 500);
      }
    };

    fetchUserData();
  }, []);

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

  const handleSubmit = async (e) => {
    e.preventDefault();

    // validation of fields before submission
    const validdrugs = drugs.filter(med => med.trim() !== '');
    const validReactions = reactions.filter(effect => effect.trim() !== '');

    if (!validdrugs.length || !validReactions.length || !user) {
      alert('Please enter at least one drug and one side reaction.');
      return;
    }

    try {
      if (isEditing) {
        // כאן נשלח בקשה לשרת לעדכון הנתונים
        /* 
        const { data, error } = await supabase
          .from('queries')
          .update({
            drugs: validdrugs,
            reactions: validreactions,
          })
          .eq('id', editingQueryId)
          .select();
        */

        // local updating
        const updatedQueries = savedQueries.map(query => {
          if (query.id === editingQueryId) {
            // fake response from supabase
            const updatedResult = `Updated result after checking ${validdrugs.length} drugs and ${validReactions.length} reactions.`;

            return {
              ...query,
              drugs: validdrugs,
              reactions: validReactions,
              result: updatedResult,
              updated_at: new Date().toISOString()
            };
          }
          return query;
        });

        setSavedQueries(updatedQueries);
        setIsEditing(false);
        setEditingQueryId(null);
      } else {
        // כאן נשלח בקשה לשרת שיעבד את הנתונים
        const result = "Sample result - analysis of the relationship between drugs and reactions";

        // במקום להכניס לדאטה-בייס, פשוט מוסיפים לסטייט המקומי
        const newQuery = {
          id: Date.now(),
          user_id: user.id,
          drugs: validdrugs,
          reactions: validReactions,
          result: result,
          created_at: new Date().toISOString()
        };

        setSavedQueries([newQuery, ...savedQueries]);
      }

      // reset fields after submission
      setdrugs(['']);
      setReactions(['']);

    } catch (error) {
      console.error('Error saving query:', error);
      alert('An error occurred while saving the query');
    }
  };

  const handleLogout = () => {
    setShowLogoutPopup(true);
    setTimeout(() => {
      localStorage.removeItem('token');
      navigate('/');
    }, 2000);
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

          <form onSubmit={handleSubmit}>
            <div className="form-section">
              <h3 className="section-label">Drugs list</h3>
              {drugs.map((drug, index) => (
                <div key={`med-${index}`} className="input-group">
                  <input
                    type="text"
                    className="input-field"
                    value={drug}
                    onChange={(e) => handleDrugChange(index, e.target.value)}
                    placeholder="Enter drug name..."
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
                  <div className="query-content">
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