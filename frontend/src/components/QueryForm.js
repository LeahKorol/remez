import React, { useState, useRef, useEffect, useCallback } from 'react';
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
    const [localErrors, setLocalErrors] = useState([]);
    const [drugSearchResults, setDrugSearchResults] = useState([]);
    const [reactionSearchResults, setReactionSearchResults] = useState([]);
    const [activeDrugSearchIndex, setActiveDrugSearchIndex] = useState(null);
    const [activeReactionSearchIndex, setActiveReactionSearchIndex] = useState(null);
    const [isButtonLoading, setIsButtonLoading] = useState(false);

    const drugSearchTimeout = useRef(null);
    const reactionSearchTimeout = useRef(null);

    // ===== Effects =====  
    useEffect(() => {
        if (resetTrigger > 0) {
            resetForm();
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
    }, [isEditing,
        initialQueryName,
        initialYearStart,
        initialYearEnd,
        initialQuarterStart,
        initialQuarterEnd,
        initialDrugs,
        initialReactions]
    );

    // Cleanup search timers
    useEffect(() => {
        return () => {
            clearTimeout(drugSearchTimeout.current);
            clearTimeout(reactionSearchTimeout.current);
        };
    }, []);

    useEffect(() => {
        if (localErrors.length > 0) {
            window.scrollTo({ top: 0, behavior: "smooth" });
        }
    }, [localErrors]);

    // ======= Handlers =======
    const resetForm = useCallback(() => {
        setQueryName("New Query");
        setYearStart("");
        setYearEnd("");
        setQuarterStart("");
        setQuarterEnd("");
        setDrugs([{ name: "", id: null }]);
        setReactions([{ name: "", id: null }]);
        setLocalErrors([]);
    }, []);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        const val = name.includes("Year") ? Number(value) : value;
        switch (name) {
            case 'queryName':
                setQueryName(value);
                break;
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
            default:
                break;
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
            const url = `http://127.0.0.1:8000/api/v1/analysis/drug-names/search/${encodeURIComponent(prefix)}/`;
            const response = await fetchWithRefresh(url);
            if (response.ok) {
                const data = await response.json();
                setDrugSearchResults(data);
                setActiveDrugSearchIndex(index);
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
        clearTimeout(drugSearchTimeout.current);
        drugSearchTimeout.current = setTimeout(() => searchDrugs(value, index), 350);
    };

    const selectDrug = (drug) => {
        if (activeDrugSearchIndex === null) return;
        const newDrugs = [...drugs];
        const duplicate = drugs.some(
            (d, i) => i !== activeDrugSearchIndex && d.name.toLowerCase() === drug.name.toLowerCase()
        );
        if (duplicate) {
            showToastMessage?.("Drug already added");
            return;
        }
        const updated = [...drugs];
        updated[activeDrugSearchIndex] = { name: drug.name, id: drug.id };
        setDrugs(updated);
        setActiveDrugSearchIndex(null);
        setDrugSearchResults([]);
    };

    const addDrug = () => {
        // check if there are any empty drug fields
        if (drugs.some((d) => !d.name.trim())) {
            showToastMessage?.("Please fill the existing drug field first");
            return;
        }
        setDrugs([...drugs, { name: '', id: null }]);
    };

    const removeDrug = (index) => {
        // if there is only one box - clear only content
        if (drugs.length === 1) {
            setDrugs([{ name: "", id: null }]);
        } else {
            setDrugs(drugs.filter((_, i) => i !== index));
        }
        setDrugSearchResults([]);
    };

    // ===== Reactions =====
    const searchReactions = async (prefix, index) => {
        if (!prefix.trim() || prefix.trim().length < 3) {
            setReactionSearchResults([]);
            setActiveReactionSearchIndex(null);
            return;
        }
        try {
            const url = `http://127.0.0.1:8000/api/v1/analysis/reaction-names/search/${encodeURIComponent(prefix)}/`;
            const response = await fetchWithRefresh(url);
            if (response.ok) {
                const data = await response.json();
                setReactionSearchResults(data);
                setActiveReactionSearchIndex(index);
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
        clearTimeout(reactionSearchTimeout.current);
        reactionSearchTimeout.current = setTimeout(() => searchReactions(value, index), 350);
    };

    const selectReaction = (reaction) => {
        if (activeReactionSearchIndex === null) return;
        const newReactions = [...reactions];
        const duplicate = reactions.some(
            (r, i) => i !== activeReactionSearchIndex && r.name.toLowerCase() === reaction.name.toLowerCase()
        );
        if (duplicate) {
            showToastMessage?.("Reaction already added");
            return;
        }
        const updated = [...reactions];
        updated[activeReactionSearchIndex] = { name: reaction.name, id: reaction.id };
        setReactions(updated);
        setActiveReactionSearchIndex(null);
        setReactionSearchResults([]);
    };

    const addReaction = () => {
        // check if there are any empty drug fields
        if (reactions.some((r) => !r.name.trim())) {
            showToastMessage?.("Please fill the existing reaction field first");
            return;
        }
        setReactions([...reactions, { name: '', id: null }]);
    };

    const removeReaction = (index) => {
        // if there is only one box - clear only content
        if (reactions.length === 1) {
            setReactions([{ name: "", id: null }]);
        } else {
            setReactions(reactions.filter((_, i) => i !== index));
        }
        setReactionSearchResults([]);
    };

    // === Errors from API ===
    function extractApiErrors(error) {
        const res = error?.response;
        const d = res?.data;
        if (d && typeof d === "object") {
            const messages = Object.entries(d).flatMap(([key, val]) =>
                Array.isArray(val)
                    ? val.map((v) => `${key}: ${v}`)
                    : typeof val === "string"
                        ? [`${key}: ${val}`]
                        : []
            );
            if (messages.length) return messages;
        }
        return [res?.statusText || error?.message || "Request failed"];
    }

    // ===== Submit =====
    const handleSubmit = async (e) => {
        e.preventDefault();
        if (isButtonLoading) return; // if already submitting, do nothing
        setIsButtonLoading(true);

        const CURRENT_YEAR = new Date().getFullYear();
        const yStart = Number(yearStart);
        const yEnd = Number(yearEnd);
        const errors = [];

        // client-side validation
        if (!queryName.trim()) errors.push('Query Name is required');
        if (!yearStart) errors.push('Start Year is required');
        if (!yearEnd) errors.push('End Year is required');
        if (!quarterStart) errors.push('Start Quarter is required');
        if (!quarterEnd) errors.push('End Quarter is required');
        if (drugs.every(d => !d.name)) errors.push('At least one drug is required');
        if (reactions.every(r => !r.name)) errors.push('At least one reaction is required');
        if (yStart && yEnd && yStart > yEnd) errors.push('Start Year must be <= End Year');
        if (yStart > CURRENT_YEAR) errors.push(`Start Year must be <= ${CURRENT_YEAR}`);
        if (yEnd > CURRENT_YEAR) errors.push(`End Year must be <= ${CURRENT_YEAR}`);
        if (yStart === yEnd && Number(quarterStart) > Number(quarterEnd)) {
            errors.push('When years are equal, Start Quarter must be <= End Quarter');
        }

        if (errors.length) {
            // id uniqueness ensures proper handling in ToastNotification
            const newErrObjs = errors.map((msg) => ({
                id: `err-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
                message: msg,
            }));
            // adding to existing errors (if any) to show all at once
            setLocalErrors(prev => [...prev, ...newErrObjs]);
            // don't call again to TastNotification - it's already done in the render
            return;
        }

        setLocalErrors([]);

        try {
            await onSubmit({
                queryName,
                yearStart: yStart,
                yearEnd: yEnd,
                quarterStart,
                quarterEnd,
                drugs,
                reactions,
            });

        } catch (err) {
            const msgs = extractApiErrors(err);
            const newErrObjs = msgs.map((msg) => ({
                id: `err-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
                message: msg,
            }));
            setLocalErrors((prev) => [...prev, ...newErrObjs]);
        }
        finally {
            setIsButtonLoading(false);
        }
    };

    // ===== Render =====
    return (
        <div className="form-wrapper">
            <form onSubmit={handleSubmit}>
                {localErrors.length > 0 && (
                    <div className="error-container">
                        {localErrors.map((errObj, idx) => (
                            <ToastNotification
                                key={errObj.id}
                                id={errObj.id}
                                message={errObj.message}
                                type="error"
                                index={idx}
                                duration={8000}
                                onClose={(id) => setLocalErrors(prev => prev.filter(e => e.id !== id))}
                            />
                        ))}
                    </div>
                )}

                <div className="form-section">
                    <div className="form-field">
                        <label htmlFor="queryName">Query Name</label>
                        <input
                            id="queryName"
                            type="text"
                            name="queryName"
                            value={queryName}
                            onChange={handleInputChange}
                            className="input-field"
                            required
                        />

                        <div className="row">
                            <div className="form-field" style={{ flex: 1 }}>
                                <label htmlFor="startYear">Start Year</label>
                                <input
                                    id="startYear"
                                    type="number"
                                    name="startYear"
                                    min="2000"
                                    max={new Date().getFullYear()}
                                    value={yearStart}
                                    onChange={handleInputChange}
                                    className="input-field"
                                    required
                                />
                            </div>

                            <div className="form-field" style={{ flex: 1 }}>
                                <label htmlFor="endYear">End Year</label>
                                <input
                                    id='endYear'
                                    type="number"
                                    name="endYear"
                                    min="2000"
                                    max={new Date().getFullYear()}
                                    value={yearEnd}
                                    onChange={handleInputChange}
                                    className="input-field"
                                    required
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

                {/* Drugs */}
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
                                <div className="search-results" role="listbox">
                                    {drugSearchResults.map((result, idx) => (
                                        <div
                                            key={idx}
                                            role="option"
                                            className="search-result-item"
                                            onClick={() => selectDrug(result)}
                                        >
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
                    <button
                        type="button"
                        className="add-button"
                        onClick={addDrug}
                    >
                        Add Drug
                        <FaPlus />
                    </button>
                </div>

                {/* Reactions */}
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
                                <div className="search-results" role="listbox">
                                    {reactionSearchResults.map((result, idx) => (
                                        <div
                                            key={idx}
                                            role="option"
                                            className="search-result-item"
                                            onClick={() => selectReaction(result)}
                                        >
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
                    <button
                        type="button"
                        className="add-button"
                        onClick={addReaction}
                    >
                        Add Reaction
                        <FaPlus />
                    </button>
                </div>

                {/* Submit / Cancel */}
                <div className="submit-container">
                    <button
                        type="submit"
                        className={`submit-button ${isButtonLoading || isSubmitting ? 'disabled' : ''}`}
                        disabled={
                            isButtonLoading ||
                            isSubmitting ||
                            drugs.every(d => !d.name.trim()) ||
                            reactions.every(r => !r.name.trim())
                        }
                    >
                        {isButtonLoading ? (
                            <div className="spinner"></div>
                        ) : (
                            isSubmitting
                                ? (isEditing ? 'Updating...' : 'Saving...')
                                : (isEditing ? 'Update + Calc' : 'Save + Calc')
                        )}
                    </button>
                </div>
            </form>
        </div>
    );
}