// formValidation.js
export const validateQueryForm = ({
    drugs,
    reactions,
    yearStart,
    yearEnd,
    quarterStart,
    quarterEnd,
    queryName,
}) => {
    const errors = [];

    const validDrugs = drugs.filter(drug => drug.id !== null);
    const validReactions = reactions.filter(reaction => reaction.id !== null);

    const partialDrugs = drugs.filter(drug => drug.name.trim() && !drug.id);
    const partialReactions = reactions.filter(reaction => reaction.name.trim() && !reaction.id);

    if (partialDrugs.length > 0) {
        errors.push("Please select drugs from the search results dropdown, don't just type them.");
    }

    if (partialReactions.length > 0) {
        errors.push("Please select reactions from the search results dropdown, don't just type them.");
    }

    if (validDrugs.length === 0) {
        errors.push("Please select at least one drug from the search results.");
    }

    if (validReactions.length === 0) {
        errors.push("Please select at least one reaction from the search results.");
    }

    const startYearInt = parseInt(yearStart);
    const endYearInt = parseInt(yearEnd);
    const startQuarterInt = parseInt(quarterStart);
    const endQuarterInt = parseInt(quarterEnd);

    if (startYearInt === endYearInt && startQuarterInt === endQuarterInt) {
        errors.push("Analysis requires at least 2 time periods. Please select a longer time range.");
    }

    const totalPeriods = (endYearInt - startYearInt) * 4 + (endQuarterInt - startQuarterInt + 1);
    if (totalPeriods > 40) {
        errors.push("Please select a shorter time period (maximum 10 years).");
    }

    if (startYearInt > endYearInt ||
        (startYearInt === endYearInt && startQuarterInt > endQuarterInt)) {
        errors.push("Start period must be earlier than or equal to the end period.");
    }

    if (!queryName.trim() || queryName.trim().length < 3) {
        errors.push("Please provide a meaningful name for your query (at least 3 characters).");
    }

    return errors;
};
