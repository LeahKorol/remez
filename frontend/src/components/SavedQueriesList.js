import React from 'react';
import { FaEye, FaEdit, FaTrash } from 'react-icons/fa';
import '../Pages/UserProfile.css'

const SavedQueriesList = ({
  savedQueries = [],
  onViewQuery,
  onEditQuery,
  onDeleteQuery
}) => {
  if (savedQueries.length === 0) {
    return <p className="no-queries">No Queries</p>;
  }

  return (
    <div className="queries-list">
      {savedQueries.map((item) => (
        <div key={item.id} className="query-card">
          <div className="query-item">
            <span className="query-name">{item.name}</span>
            <div className="query-actions">
              <button
                type="button"
                className="action-button view-button"
                onClick={() => onViewQuery(item)}
                title="View Details"
              >
                <FaEye />
              </button>

              <button
                type="button"
                className="action-button edit-button"
                onClick={() => onEditQuery(item)}
                title="Edit Query"
              >
                <FaEdit />
              </button>

              <button
                type="button"
                className="action-button delete-button"
                onClick={() => onDeleteQuery(item.id)}
                title="Delete Query"
              >
                <FaTrash />
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default SavedQueriesList;