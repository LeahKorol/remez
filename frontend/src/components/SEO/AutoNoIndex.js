import React from 'react';
import { Helmet } from 'react-helmet-async'; // או 'react-helmet'
import { useLocation } from 'react-router-dom';

/**
 * component adds noindex meta tags to all pages
 * put <AutoNoIndex /> inside your Router but outside your Routes
 */
const AutoNoIndex = () => {
  const location = useLocation();
  
  // only allow files in the allowedPaths array to be indexed
  const allowedPaths = ['/'];
  
  const shouldNoIndex = !allowedPaths.includes(location.pathname);

  if (!shouldNoIndex) {
    return null; // do not render anything if indexing is allowed
  }

  return (
    <Helmet>
      <meta name="robots" content="noindex, nofollow" />
      <meta name="googlebot" content="noindex, nofollow" />
    </Helmet>
  );
};

export default AutoNoIndex;