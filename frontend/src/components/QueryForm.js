<<<<<<< HEAD
import React, { useState, useRef } from 'react';
import { FaPlus, FaTimes } from 'react-icons/fa';
import CustomSelect from './CustomSelect';
import ToastNotification from './ToastNotification';
import { fetchWithRefresh } from '../utils/tokenService';
import '../Pages/UserProfile.css';

export default function QueryForm({ onSubmit, onCancel, showToastMessage, isEditing, isSubmitting, submitError }) {
    // Form state
    const [queryName, setQueryName] = useState('New Query');
    const [yearStart, setYearStart] = useState('');
    const [yearEnd, setYearEnd] = useState('');
    const [quarterStart, setQuarterStart] = useState('');
    const [quarterEnd, setQuarterEnd] = useState('');
    const [drugs, setDrugs] = useState([{ name: '', id: null }]);
    const [reactions, setReactions] = useState([{ name: '', id: null }]);

    // Search state
    const [drugSearchResults, setDrugSearchResults] = useState([]);
    const [reactionSearchResults, setReactionSearchResults] = useState([]);
    const [activeDrugSearchIndex, setActiveDrugSearchIndex] = useState(null);
    const [activeReactionSearchIndex, setActiveReactionSearchIndex] = useState(null);

    const [localErrors, setLocalErrors] = useState([]);

    const drugSearchTimeout = useRef(null);
    const reactionSearchTimeout = useRef(null);

    // ======= Handlers =======
    const handleInputChange = (e) => {
        const { name, value } = e.target;
        switch (name) {
            case 'queryName': setQueryName(value); break;
            case 'startYear': setYearStart(value); break;
            case 'endYear': setYearEnd(value); break;
            case 'startQuarter': setQuarterStart(value); break;
            case 'endQuarter': setQuarterEnd(value); break;
            default: break;
        }
    };

    // ===== Drugs =====
    const searchDrugs = async (prefix, index) => {
        if (!prefix.trim() || prefix.trim().length < 3) {
            setDrugSearchResults([]);
            setActiveDrugSearchIndex(null);
            return;
        }
        try {
            const response = await fetchWithRefresh(`http://127.0.0.1:8000/api/v1/analysis/drug-names/search/${prefix}/`);
            if (response.ok) {
                const data = await response.json();
                setDrugSearchResults(data);
                setActiveDrugSearchIndex(index);
            } else {
                setDrugSearchResults([]);
            }
        } catch (error) {
            console.error('Drug search error:', error);
            setDrugSearchResults([]);
        }
    };

    const handleDrugChange = (index, value) => {
        const newDrugs = [...drugs];
        newDrugs[index] = { name: value, id: null };
        setDrugs(newDrugs);

        if (drugSearchTimeout.current) clearTimeout(drugSearchTimeout.current);
        drugSearchTimeout.current = setTimeout(() => searchDrugs(value, index), 300);
    };

    const selectDrug = (drug) => {
        if (activeDrugSearchIndex === null) return;
        const newDrugs = [...drugs];
        newDrugs[activeDrugSearchIndex] = { name: drug.name, id: drug.id };
        setDrugs(newDrugs);
        setActiveDrugSearchIndex(null);
        setDrugSearchResults([]);
    };

    const addDrug = () => setDrugs([...drugs, { name: '', id: null }]);
    const removeDrug = (index) => setDrugs(drugs.filter((_, i) => i !== index));

    // ===== Reactions =====
    const searchReactions = async (prefix, index) => {
        if (!prefix.trim() || prefix.trim().length < 3) {
            setReactionSearchResults([]);
            setActiveReactionSearchIndex(null);
            return;
        }
        try {
            const response = await fetchWithRefresh(`http://127.0.0.1:8000/api/v1/analysis/reaction-names/search/${prefix}/`);
            if (response.ok) {
                const data = await response.json();
                setReactionSearchResults(data);
                setActiveReactionSearchIndex(index);
            } else {
                setReactionSearchResults([]);
            }
        } catch (error) {
            console.error('Reaction search error:', error);
            setReactionSearchResults([]);
        }
    };

    const handleReactionChange = (index, value) => {
        const newReactions = [...reactions];
        newReactions[index] = { name: value, id: null };
        setReactions(newReactions);

        if (reactionSearchTimeout.current) clearTimeout(reactionSearchTimeout.current);
        reactionSearchTimeout.current = setTimeout(() => searchReactions(value, index), 300);
    };

    const selectReaction = (reaction) => {
        if (activeReactionSearchIndex === null) return;
        const newReactions = [...reactions];
        newReactions[activeReactionSearchIndex] = { name: reaction.name, id: reaction.id };
        setReactions(newReactions);
        setActiveReactionSearchIndex(null);
        setReactionSearchResults([]);
    };

    const addReaction = () => setReactions([...reactions, { name: '', id: null }]);
    const removeReaction = (index) => setReactions(reactions.filter((_, i) => i !== index));

    // ===== Submit =====
    const handleSubmit = (e) => {
        if (e && typeof e.preventDefault === 'function') {
            e.preventDefault();
        }

        const errors = [];
        if (!queryName.trim()) errors.push('Query Name is required');
        if (!yearStart) errors.push('Start Year is required');
        if (!yearEnd) errors.push('End Year is required');
        if (!quarterStart) errors.push('Start Quarter is required');
        if (!quarterEnd) errors.push('End Quarter is required');
        if (drugs.every(d => !d.name)) errors.push('At least one drug is required');
        if (reactions.every(r => !r.name)) errors.push('At least one reaction is required');

        if (errors.length > 0) {
            setLocalErrors(errors);
            errors.forEach(err => showToastMessage && showToastMessage(err));
            return;
        }

        setLocalErrors([]);
        onSubmit(e, {queryName, yearStart, yearEnd, quarterStart, quarterEnd, drugs, reactions});
    };


    // ===== Render =====
    return (
        <form onSubmit={handleSubmit}>
            {localErrors.length > 0 && (
                <div className="error-container">
                    {localErrors.map((err, idx) => (
                        <ToastNotification key={idx} message={err} type="error" />
                    ))}
                </div>
            )}

=======
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
>>>>>>> f411e9f61f5caa78d223766188e47a90ddafbb00
            <div className="form-section">
                <div className="form-field">
                    <div className="mb-2">
                        <label className="block text-sm font-medium text-gray-700">Query Name</label>
                        <input
                            type="text"
                            name="queryName"
                            value={queryName}
<<<<<<< HEAD
                            onChange={handleInputChange}
=======
                            onChange={(e) => showToastMessage(e.target.value)}
>>>>>>> f411e9f61f5caa78d223766188e47a90ddafbb00
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
<<<<<<< HEAD
                            onChange={handleInputChange}
=======
                            onChange={(e) => showToastMessage(e.target.value)}
>>>>>>> f411e9f61f5caa78d223766188e47a90ddafbb00
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
<<<<<<< HEAD
                            onChange={handleInputChange}
=======
                            onChange={(e) => showToastMessage(e.target.value)}
>>>>>>> f411e9f61f5caa78d223766188e47a90ddafbb00
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                        />
                    </div>

                    <div className="mb-2">
                        <label className="block text-sm font-medium text-gray-700">Start Quarter</label>
                        <CustomSelect
                            name="startQuarter"
                            value={quarterStart}
<<<<<<< HEAD
                            onChange={handleInputChange}
=======
                            onChange={(e) => showToastMessage(e.target.value)}
>>>>>>> f411e9f61f5caa78d223766188e47a90ddafbb00
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
<<<<<<< HEAD
                            onChange={handleInputChange}
=======
                            onChange={(e) => showToastMessage(e.target.value)}
>>>>>>> f411e9f61f5caa78d223766188e47a90ddafbb00
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
<<<<<<< HEAD
            </div>

            <div className="form-section">
=======

>>>>>>> f411e9f61f5caa78d223766188e47a90ddafbb00
                <h3 className="section-label">Drugs List</h3>
                {drugs.map((drug, index) => (
                    <div key={`drug-${index}`} className="input-group">
                        <input
                            type="text"
                            className="input-field"
                            value={drug.name}
<<<<<<< HEAD
                            onChange={(e) => handleDrugChange(index, e.target.value)}
=======
                            onChange={(e) => onDrugChange(index, e.target.value)}
>>>>>>> f411e9f61f5caa78d223766188e47a90ddafbb00
                            placeholder="Enter a drug..."
                            dir="ltr"
                        />
                        {activeDrugSearchIndex === index && drugSearchResults.length > 0 && (
                            <div className="search-results">
<<<<<<< HEAD
                                {drugSearchResults.map((result, idx) => (
                                    <div key={idx} className="search-result-item" onClick={() => selectDrug(result)}>
=======
                                {drugSearchResults.map((result, resultIndex) => (
                                    <div
                                        key={resultIndex}
                                        className="search-result-item"
                                        onClick={() => onDrugChange(index, result.name)}
                                    >
>>>>>>> f411e9f61f5caa78d223766188e47a90ddafbb00
                                        {result.name}
                                    </div>
                                ))}
                            </div>
                        )}
                        {(index > 0 || drugs.length > 1) && (
<<<<<<< HEAD
                            <button type="button" className="remove-button" onClick={() => removeDrug(index)}>
=======
                            <button
                                type="button"
                                className="remove-button"
                                onClick={() => removeDrug(index)}
                            >
>>>>>>> f411e9f61f5caa78d223766188e47a90ddafbb00
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
<<<<<<< HEAD
                            onChange={(e) => handleReactionChange(index, e.target.value)}
=======
                            onChange={(e) => onReactionChange(index, e.target.value)}
>>>>>>> f411e9f61f5caa78d223766188e47a90ddafbb00
                            placeholder="Enter a reaction..."
                            dir="ltr"
                        />
                        {activeReactionSearchIndex === index && reactionSearchResults.length > 0 && (
                            <div className="search-results">
<<<<<<< HEAD
                                {reactionSearchResults.map((result, idx) => (
                                    <div key={idx} className="search-result-item" onClick={() => selectReaction(result)}>
=======
                                {reactionSearchResults.map((result, resultIndex) => (
                                    <div
                                        key={resultIndex}
                                        className="search-result-item"
                                        onClick={() => onReactionChange(index, result.name)}
                                    >
>>>>>>> f411e9f61f5caa78d223766188e47a90ddafbb00
                                        {result.name}
                                    </div>
                                ))}
                            </div>
                        )}
                        {(index > 0 || reactions.length > 1) && (
<<<<<<< HEAD
                            <button type="button" className="remove-button" onClick={() => removeReaction(index)}>
=======
                            <button
                                type="button"
                                className="remove-button"
                                onClick={() => removeReaction(index)}
                            >
>>>>>>> f411e9f61f5caa78d223766188e47a90ddafbb00
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
<<<<<<< HEAD
                <button type="submit" className="submit-button" disabled={isSubmitting}>
=======
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
>>>>>>> f411e9f61f5caa78d223766188e47a90ddafbb00
                    {isSubmitting ? (isEditing ? 'Updating...' : 'Saving...') : (isEditing ? 'Update + Calc' : 'Save + Calc')}
                </button>
                {isEditing && (
                    <button type="button" className="cancel-button" onClick={onCancel}>
                        Cancel
                    </button>
                )}
            </div>
<<<<<<< HEAD
        </form>
    );
}
=======

            <ToastNotification message={submitError} type="error" />
        </form>
    );
}
>>>>>>> f411e9f61f5caa78d223766188e47a90ddafbb00
