import React, { useState, useRef, useEffect } from 'react';
import { FaPlus, FaTimes } from 'react-icons/fa';
import CustomSelect from './CustomSelect';
import ToastNotification from './ToastNotification';
import { fetchWithRefresh } from '../utils/tokenService';
import '../Pages/UserProfile.css';

export default function QueryForm({
    onSubmit,
    onCancel,
    showToastMessage,
    isEditing,
    isSubmitting,
    resetTrigger,
    queryName: initialQueryName,
    yearStart: initialYearStart,
    yearEnd: initialYearEnd,
    quarterStart: initialQuarterStart,
    quarterEnd: initialQuarterEnd,
    drugs: initialDrugs,
    reactions: initialReactions, }) {

    // Form state
    const [queryName, setQueryName] = useState('New Query');
    const [yearStart, setYearStart] = useState('');
    const [yearEnd, setYearEnd] = useState('');
    const [quarterStart, setQuarterStart] = useState('');
    const [quarterEnd, setQuarterEnd] = useState('');
    const [drugs, setDrugs] = useState([{ name: '', id: null }]);
    const [reactions, setReactions] = useState([{ name: '', id: null }]);

    useEffect(() => {
        if (resetTrigger > 0) {
            setQueryName('New Query');
            setYearStart('');
            setYearEnd('');
            setQuarterStart('');
            setQuarterEnd('');
            setDrugs([{ name: '', id: null }]);
            setReactions([{ name: '', id: null }]);
        }
    }, [resetTrigger]);

    useEffect(() => {
        if (isEditing) {
            setQueryName(initialQueryName || 'New Query');
            setYearStart(initialYearStart || '');
            setYearEnd(initialYearEnd || '');
            setQuarterStart(initialQuarterStart || '');
            setQuarterEnd(initialQuarterEnd || '');
            setDrugs(initialDrugs && initialDrugs.length > 0 ? initialDrugs : [{ name: '', id: null }]);
            setReactions(initialReactions && initialReactions.length > 0 ? initialReactions : [{ name: '', id: null }]);
        }
    }, [isEditing, initialQueryName, initialYearStart, initialYearEnd, initialQuarterStart, initialQuarterEnd, initialDrugs, initialReactions]);


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
            // 💬 תיקון ל-template literal
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
    const removeDrug = (index) => {
        const updatedDrugs = drugs.filter((_, i) => i !== index);
        setDrugs(updatedDrugs);

        if (updatedDrugs.length === 0) {
            showToastMessage('At least one drug is required');
        }
    };

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
    const removeReaction = (index) => {
        const updatedReactions = reactions.filter((_, i) => i !== index);
        setReactions(updatedReactions);

        if (updatedReactions.length === 0) {
            showToastMessage('At least one reaction is required');
        }
    };

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
        onSubmit(e, { queryName, yearStart, yearEnd, quarterStart, quarterEnd, drugs, reactions });
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

            <div className="form-section">
                <div className="form-field">
                    <label>Query Name</label>
                    <input
                        type="text"
                        name="queryName"
                        value={queryName}
                        onChange={handleInputChange}
                        className="input-field"
                    />

                    <div className="row">
                        <div className="form-field" style={{ flex: 1 }}>
                            <label>Start Year</label>
                            <input
                                type="number"
                                name="startYear"
                                value={yearStart}
                                onChange={handleInputChange}
                                className="input-field"
                            />
                        </div>

                        <div className="form-field" style={{ flex: 1 }}>
                            <label>End Year</label>
                            <input
                                type="number"
                                name="endYear"
                                value={yearEnd}
                                onChange={handleInputChange}
                                className="input-field"
                            />
                        </div>
                    </div>

                    <div className="row">
                        <div className="form-field" style={{ flex: 1 }}>
                            <label>Start Quarter</label>
                            <CustomSelect
                                name="startQuarter"
                                value={quarterStart}
                                onChange={handleInputChange}
                                options={[
                                    { value: "1", label: "Quarter 1" },
                                    { value: "2", label: "Quarter 2" },
                                    { value: "3", label: "Quarter 3" },
                                    { value: "4", label: "Quarter 4" },
                                ]}
                            />
                        </div>

                        <div className="form-field" style={{ flex: 1 }}>
                            <label>End Quarter</label>
                            <CustomSelect
                                name="endQuarter"
                                value={quarterEnd}
                                onChange={handleInputChange}
                                options={[
                                    { value: "1", label: "Quarter 1" },
                                    { value: "2", label: "Quarter 2" },
                                    { value: "3", label: "Quarter 3" },
                                    { value: "4", label: "Quarter 4" },
                                ]}
                            />
                        </div>
                    </div>
                </div>
            </div>

            <div className="form-section">
                <h3 className="section-label">Drugs List</h3>
                {drugs.map((drug, index) => (
                    <div key={`drug-${index}`} className="input-group">
                        <input
                            type="text"
                            className="input-field"
                            value={drug.name}
                            onChange={(e) => handleDrugChange(index, e.target.value)}
                            placeholder="Enter a drug..."
                        />
                        {activeDrugSearchIndex === index && drugSearchResults.length > 0 && (
                            <div className="search-results">
                                {drugSearchResults.map((result, idx) => (
                                    <div key={idx} className="search-result-item" onClick={() => selectDrug(result)}>
                                        {result.name}
                                    </div>
                                ))}
                            </div>
                        )}
                        <button
                            type="button"
                            className="remove-button"
                            onClick={() => removeDrug(index)}
                        >
                            <FaTimes />
                        </button>
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
                            onChange={(e) => handleReactionChange(index, e.target.value)}
                            placeholder="Enter a reaction..."
                        />
                        {activeReactionSearchIndex === index && reactionSearchResults.length > 0 && (
                            <div className="search-results">
                                {reactionSearchResults.map((result, idx) => (
                                    <div key={idx} className="search-result-item" onClick={() => selectReaction(result)}>
                                        {result.name}
                                    </div>
                                ))}
                            </div>
                        )}
                        <button
                            type="button"
                            className="remove-button"
                            onClick={() => removeReaction(index)}
                        >
                            <FaTimes />
                        </button>
                    </div>
                ))}
                <button type="button" className="add-button" onClick={addReaction}>
                    Add Reaction <FaPlus />
                </button>
            </div>

            <div className="submit-container">
                <button
                    type="submit"
                    className={`submit-button ${isSubmitting ? 'disabled' : ''}`}
                    disabled={
                        isSubmitting ||
                        drugs.every(d => !d.name.trim()) ||
                        reactions.every(r => !r.name.trim())
                    }
                >
                    {isSubmitting
                        ? (isEditing ? 'Updating...' : 'Saving...')
                        : (isEditing ? 'Update + Calc' : 'Save + Calc')}
                </button>
            </div>
        </form>
    );
}