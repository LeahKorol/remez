import React from 'react';
import { FaEye, FaEdit, FaTrash } from 'react-icons/fa';
import '../Pages/UserProfile.css'

const SavedQueriesList = ({
  savedQueries = [],
  onViewQuery,
  onEditQuery,
  onDeleteQuery,
  editingQueryId,
  isEditing,
  editingQueryLoading,
  viewingQueryId
}) => {

  const isQueryLocked = (query) => {
    // if the query is currently being edited, it should not be locked
    if (editingQueryId && query.id === editingQueryId) {
      console.log("🔓 Query unlocked - currently editing:", query.id);
      return false;
    }

    const resultStatus = query?.result?.status;
    const queryStatus = query?.status;
    const status = resultStatus || queryStatus;

    console.log("🔒 isQueryLocked check:", {
      queryId: query.id,
      queryStatus: queryStatus,
      resultStatus: resultStatus,
      finalStatus: status,
      isLocked: status && status !== "completed" && status !== "failed"
    });

    return status && status !== "completed" && status !== "failed";
  };

  if (savedQueries.length === 0) {
    return <p className="no-queries">No Queries</p>;
  }

  return (
    <div className="queries-list">
      {savedQueries.map((item) => (
        <div key={item.id} className="query-card">
          <div className="query-item">
            <span
              className="query-name"
              style={{
                color: item.id === viewingQueryId ? "#7b5dc7" : "inherit"
              }}
            >
              {item.name}
            </span>
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
                disabled={isQueryLocked(item)}
                title={
                  isQueryLocked(item)
                    ? "Query is still processing. Edit disabled."
                    : editingQueryLoading
                      ? "Loading query..."
                      : "Edit query"
                }
                className="action-button edit-button"
                onClick={() => onEditQuery(item)}
              >
                <FaEdit />
              </button>

              <button
                type="button"
                disabled={isQueryLocked(item)}
                className="action-button delete-button"
                onClick={() => onDeleteQuery(item.id)}
                title={isQueryLocked(item) ? "Query is still processing. Delete disabled." : "Delete Query"}
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