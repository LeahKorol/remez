import React from 'react';
import { FaPlus, FaTimes } from 'react-icons/fa';
import CustomSelect from './CustomSelect';
import ToastNotification from './ToastNotification';
import '../Pages/UserProfile.css'

export default function QueryForm({
    drugs,
    reactions,
    yearStart,
    yearEnd,
    quarterStart,
    quarterEnd,
    queryName,
    isEditing,
    isSubmitting,
    submitError,
    showToastMessage,
    onSubmit,
    onCancel,
    onDrugChange,
    onReactionChange,
    addDrug,
    addReaction,
    removeDrug,
    removeReaction,
    activeDrugSearchIndex,
    activeReactionSearchIndex,
    drugSearchResults,
    reactionSearchResults,
}) {
    return (
        <form onSubmit={onSubmit}>
            <div className="form-section">
                <div className="form-field">
                    <div className="mb-2">
                        <label className="block text-sm font-medium text-gray-700">Query Name</label>
                        <input
                            type="text"
                            name="queryName"
                            value={queryName}
                            onChange={(e) => showToastMessage(e.target.value)}
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
                            onChange={(e) => showToastMessage(e.target.value)}
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
                            onChange={(e) => showToastMessage(e.target.value)}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                        />
                    </div>

                    <div className="mb-2">
                        <label className="block text-sm font-medium text-gray-700">Start Quarter</label>
                        <CustomSelect
                            name="startQuarter"
                            value={quarterStart}
                            onChange={(e) => showToastMessage(e.target.value)}
                            placeholder="Select Quarter"
                            options={[
                                { value: "1", label: "Quarter 1" },
                                { value: "2", label: "Quarter 2" },
                                { value: "3", label: "Quarter 3" },
                                { value: "4", label: "Quarter 4" },
                            ]}
                        />
                    </div>

                    <div className="mb-2">
                        <label className="block text-sm font-medium text-gray-700">End Quarter</label>
                        <CustomSelect
                            name="endQuarter"
                            value={quarterEnd}
                            onChange={(e) => showToastMessage(e.target.value)}
                            placeholder="Select Quarter"
                            options={[
                                { value: "1", label: "Quarter 1" },
                                { value: "2", label: "Quarter 2" },
                                { value: "3", label: "Quarter 3" },
                                { value: "4", label: "Quarter 4" },
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
                            onChange={(e) => onDrugChange(index, e.target.value)}
                            placeholder="Enter a drug..."
                            dir="ltr"
                        />
                        {activeDrugSearchIndex === index && drugSearchResults.length > 0 && (
                            <div className="search-results">
                                {drugSearchResults.map((result, resultIndex) => (
                                    <div
                                        key={resultIndex}
                                        className="search-result-item"
                                        onClick={() => onDrugChange(index, result.name)}
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
                                onClick={() => removeDrug(index)}
                            >
                                <FaTimes />
                            </button>
                        )}
                    </div>
                ))}
                <button type="button" className="add-button" onClick={addDrug}>
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
                            onChange={(e) => onReactionChange(index, e.target.value)}
                            placeholder="Enter a reaction..."
                            dir="ltr"
                        />
                        {activeReactionSearchIndex === index && reactionSearchResults.length > 0 && (
                            <div className="search-results">
                                {reactionSearchResults.map((result, resultIndex) => (
                                    <div
                                        key={resultIndex}
                                        className="search-result-item"
                                        onClick={() => onReactionChange(index, result.name)}
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
                                onClick={() => removeReaction(index)}
                            >
                                <FaTimes />
                            </button>
                        )}
                    </div>
                ))}
                <button type="button" className="add-button" onClick={addReaction}>
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
                    disabled={isSubmitting}
                >
                    {isSubmitting ? (isEditing ? 'Updating...' : 'Saving...') : (isEditing ? 'Update + Calc' : 'Save + Calc')}
                </button>
                {isEditing && (
                    <button type="button" className="cancel-button" onClick={onCancel}>
                        Cancel
                    </button>
                )}
            </div>

            <ToastNotification message={submitError} type="error" />
        </form>
    );
}