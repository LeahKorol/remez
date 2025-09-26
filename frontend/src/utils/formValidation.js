export const validateQueryForm = ({
    drugs,
    reactions,
    yearStart,
    yearEnd,
    quarterStart,
    quarterEnd,
    queryName,
    setSubmitError
}) => {
    setSubmitError('');

    const validDrugs = drugs.filter(drug => drug.id !== null);
    const validReactions = reactions.filter(reaction => reaction.id !== null);

    const partialDrugs = drugs.filter(drug => drug.name.trim() && !drug.id);
    const partialReactions = reactions.filter(reaction => reaction.name.trim() && !reaction.id);

    if (partialDrugs.length > 0) {
        setSubmitError("Please select drugs from the search results dropdown, don't just type them.");
        return false;
    }

    if (partialReactions.length > 0) {
        setSubmitError("Please select reactions from the search results dropdown, don't just type them.");
        return false;
    }

    if (validDrugs.length === 0) {
        setSubmitError("Please select at least one drug from the search results.");
        return false;
    }

    if (validReactions.length === 0) {
        setSubmitError("Please select at least one reaction from the search results.");
        return false;
    }

    const startYearInt = parseInt(yearStart);
    const endYearInt = parseInt(yearEnd);
    const startQuarterInt = parseInt(quarterStart);
    const endQuarterInt = parseInt(quarterEnd);

    if (startYearInt === endYearInt && startQuarterInt === endQuarterInt) {
        setSubmitError("Analysis requires at least 2 time periods. Please select a longer time range.");
        return false;
    }

    const totalPeriods = (endYearInt - startYearInt) * 4 + (endQuarterInt - startQuarterInt + 1);
    if (totalPeriods > 40) {
        setSubmitError("Please select a shorter time period (maximum 10 years).");
        return false;
    }

    if (parseInt(startYearInt) > parseInt(endYearInt) ||
        (parseInt(startYearInt) === parseInt(endYearInt) && parseInt(startQuarterInt) > parseInt(endQuarterInt))) {
        setSubmitError('Start period must be earlier than or equal to the end period.');
        return false;
    }

    if (!queryName.trim() || queryName.trim().length < 3) {
        setSubmitError("Please provide a meaningful name for your query (at least 3 characters).");
        return false;
    }

    return true;
};
