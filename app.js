document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search');
    const websiteSelect = document.getElementById('websiteSelect');
    const refreshBtn = document.getElementById('refresh');
    const dateFilter = document.getElementById('dateFilter');
    const editKeywordsBtn = document.getElementById('editKeywords');
    const keywordModal = document.getElementById('keywordModal');
    const keywordsTextarea = document.getElementById('keywordsTextarea');
    const saveKeywordsBtn = document.getElementById('saveKeywords');
    const cancelEditBtn = document.getElementById('cancelEdit');
    const lawsContainer = document.getElementById('laws-container');
    const loadingDiv = document.getElementById('loading');

    let lawsData = [];
    let currentDateFilter = 'all';
    let currentWebsiteFilter = 'all';
    let availableWebsites = {};

    // Populate website selection dropdown (by category instead of individual sites)
    function populateWebsiteSelect(categories) {
        Object.keys(categories).forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category.replace(/_/g, ' ').toUpperCase();
            websiteSelect.appendChild(option);
        });
    }

    // Update fetchWebsites to handle categories
    async function fetchWebsites() {
        try {
            const response = await fetch('/api/websites');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();

            availableWebsites = data.categories || {};
            populateWebsiteSelect(availableWebsites);

        } catch (error) {
            console.error('Failed to fetch websites:', error);
        }
    }

    // Fetch laws by category
    async function fetchLawsByCategory(category) {
        try {
            loadingDiv.textContent = `Loading ${category} category laws...`;
            
            const response = await fetch(`/api/category/${category}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const result = await response.json();
            
            if (result.success) {
                // Parse all markdown files in the category
                lawsData = result.files.flatMap(file => {
                    const laws = [];
                    const content = file.content;
                    
                    // Split by law separator (---)
                    const lawSections = content.split('---\n\n');
                    
                    for (const section of lawSections) {
                        if (section.trim()) {
                            const titleMatch = section.match(/## (.+?)\n/);
                            const publishedMatch = section.match(/- \*\*Published:\*\* (.+?)\n/);
                            const linkMatch = section.match(/- \*\*Link:\*\* (.+?)\n/);
                            const scoreMatch = section.match(/- \*\*Relevance Score:\*\* (.+?)\n/);
                            const summaryMatch = section.match(/### AI Summary\n([\s\S]+?)(?=###|$)/);
                            
                            if (titleMatch) {
                                // Extract website key from filename mapping
                                const filenameToWebsiteMap = {
                                    "sso_agc_gov_sg": "sso_agc",
                                    "www_iras_gov_sg": "iras_cit",
                                    "www_acra_gov_sg": "acra_main",
                                    "acra_frs": "acra_frs",
                                    "www_singstat_gov_sg": "singstat",
                                    "www_mom_gov_sg": "mom_employment",
                                    "mom_wic": "mom_wic",
                                    "profamily_leave": "profamily_leave",
                                    "www_cpf_gov_sg": "cpf",
                                    "mom_retirement": "mom_retirement",
                                    "mom_reemployment": "mom_reemployment",
                                    "www_caas_gov_sg": "caas_air_nav",
                                    "caas_air_nav_order": "caas_air_nav_order",
                                    "www_ecfr_gov": "ecfr_part_21",
                                    "mtcr_annex": "mtcr_annex",
                                    "imda_spectrum": "imda_spectrum",
                                    "imda_telecom": "imda_telecom",
                                    "nas_gov_records": "nas_gov_records",
                                    "nas_gov_pdf": "nas_gov_pdf",
                                    "nparks_animals": "nparks_animals",
                                    "nparks_naclar": "nparks_naclar",
                                    "nparks_animals_page2": "nparks_animals_page2",
                                    "moh_biosafety": "moh_biosafety",
                                    "opcw_cwc": "opcw_cwc",
                                    "www_gmac_sg": "gmac_news",
                                    "moh_medical_acts": "moh_medical_acts",
                                    "hsa_poisons": "hsa_poisons",
                                    "hsa_controlled_drugs": "hsa_controlled_drugs",
                                    "moh_hcsa": "moh_hcsa",
                                    "mom_wsh": "mom_wsh"
                                };

                                let source = file.website_key || file.filename.replace('.md', '');
                                
                                // Parse keywords from the markdown
                                const keywordsMatch = section.match(/### Keywords Found\n([\s\S]+?)(?=###|$)/);
                                let keyword_matches = [];
                                if (keywordsMatch) {
                                    const keywordsContent = keywordsMatch[1];
                                    const keywordLines = keywordsContent.split('\n').filter(line => line.trim().startsWith('- '));
                                    keyword_matches = keywordLines.map(line => {
                                        const keyword = line.replace(/^- /, '').split('(')[0].trim();
                                        return keyword;
                                    });
                                }
                                
                                // Parse is_new status from the markdown
                                const isNewMatch = section.match(/- \*\*Is New:\*\* (.+?)\n/);
                                let is_new = true;
                                if (isNewMatch) {
                                    const isNewValue = isNewMatch[1].trim().toLowerCase();
                                    is_new = (isNewValue === 'true');
                                }
                                
                                laws.push({
                                    title: titleMatch[1].trim(),
                                    published: publishedMatch ? publishedMatch[1].trim() : 'Unknown',
                                    link: linkMatch ? linkMatch[1].trim() : '',
                                    relevance_score: scoreMatch ? parseFloat(scoreMatch[1]) : 0,
                                    ai_description: summaryMatch ? summaryMatch[1].trim() : 'No summary available',
                                    is_new: is_new,
                                    source: source,
                                    keyword_matches: keyword_matches,
                                    category: category
                                });
                            }
                        }
                    }
                    
                    return laws;
                });
                
                console.log(`Loaded ${lawsData.length} laws from ${category} category`);
                
                // Sort laws by relevance score (descending) before displaying
                lawsData.sort((a, b) => b.relevance_score - a.relevance_score);
                displayLaws(lawsData);
            } else {
                console.error('Failed to fetch category laws:', result.error);
                lawsData = [];
                displayLaws(lawsData);
            }
            
            loadingDiv.textContent = '';
        } catch (error) {
            loadingDiv.textContent = 'Error loading category laws';
            console.error('Failed to fetch category laws:', error);
            lawsData = [];
            displayLaws(lawsData);
        }
    }

    // Fetch laws data
    async function fetchLaws(dateFilter = 'all', website = 'all') {
        try {
            loadingDiv.textContent = 'Loading laws...';
            
            if (website !== 'all') {
                // Scrape specific website
                const response = await fetch('/api/scrape', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ website })
                });
                
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                const result = await response.json();
                
                // After scraping, load the markdown files
                await loadMarkdownFiles();
            } else {
                // Load existing markdown files
                await loadMarkdownFiles();
            }
            
            loadingDiv.textContent = '';
        } catch (error) {
            loadingDiv.textContent = 'Error loading laws. Please try again.';
            console.error('Fetch error details:', {
                message: error.message,
                stack: error.stack,
                type: error.name
            });
        }
    }

    // Load markdown files from server
    async function loadMarkdownFiles() {
        try {
            const response = await fetch('/api/markdown-files');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const result = await response.json();
            
            if (result.success) {
                // Convert markdown files to law objects for display
                lawsData = result.files.flatMap(file => {
                    // Parse markdown content to extract law information
                    const laws = [];
                    const content = file.content;
                    
                    // Split by law separator (---)
                    const lawSections = content.split('---\n\n');
                    
                    for (const section of lawSections) {
                        if (section.trim()) {
                            const titleMatch = section.match(/## (.+?)\n/);
                            const publishedMatch = section.match(/- \*\*Published:\*\* (.+?)\n/);
                            const linkMatch = section.match(/- \*\*Link:\*\* (.+?)\n/);
                            const scoreMatch = section.match(/- \*\*Relevance Score:\*\* (.+?)\n/);
                            const summaryMatch = section.match(/### AI Summary\n([\s\S]+?)(?=###|$)/);
                            
                            if (titleMatch) {
                                // Extract website key from filename (e.g., "sso_agc_gov_sg" -> "sso_agc")
                                let source = file.filename.replace('.md', '');
                                
                                // Create a complete mapping from filename patterns to website keys
                                const filenameToWebsiteMap = {
                                    "sso_agc_gov_sg": "sso_agc",
                                    "www_iras_gov_sg": "iras_cit",
                                    "www_acra_gov_sg": "acra_main",
                                    "acra_frs": "acra_frs",
                                    "www_singstat_gov_sg": "singstat",
                                    "www_mom_gov_sg": "mom_employment",
                                    "mom_wic": "mom_wic",
                                    "profamily_leave": "profamily_leave",
                                    "www_cpf_gov_sg": "cpf",
                                    "mom_retirement": "mom_retirement",
                                    "mom_reemployment": "mom_reemployment",
                                    "www_caas_gov_sg": "caas_air_nav",
                                    "caas_air_nav_order": "caas_air_nav_order",
                                    "www_ecfr_gov": "ecfr_part_21",
                                    "mtcr_annex": "mtcr_annex",
                                    "imda_spectrum": "imda_spectrum",
                                    "imda_telecom": "imda_telecom",
                                    "nas_gov_records": "nas_gov_records",
                                    "nas_gov_pdf": "nas_gov_pdf",
                                    "nparks_animals": "nparks_animals",
                                    "nparks_naclar": "nparks_naclar",
                                    "nparks_animals_page2": "nparks_animals_page2",
                                    "moh_biosafety": "moh_biosafety",
                                    "opcw_cwc": "opcw_cwc",
                                    "gmac_news": "gmac_news",
                                    "moh_medical_acts": "moh_medical_acts",
                                    "hsa_poisons": "hsa_poisons",
                                    "hsa_controlled_drugs": "hsa_controlled_drugs",
                                    "moh_hcsa": "moh_hcsa",
                                    "mom_wsh": "mom_wsh"
                                };

                                
                                // Use mapping or fallback to filename (try to match partial names)
                                let websiteKey = filenameToWebsiteMap[source];
                                if (!websiteKey) {
                                    // Try to find a partial match
                                    for (const [filenamePattern, key] of Object.entries(filenameToWebsiteMap)) {
                                        if (source.includes(filenamePattern.replace('www_', '').replace('_gov_sg', ''))) {
                                            websiteKey = key;
                                            break;
                                        }
                                    }
                                    // If still not found, use the source as is
                                    if (!websiteKey) {
                                        websiteKey = source;
                                    }
                                }
                                
                                // Parse keywords from the markdown
                                const keywordsMatch = section.match(/### Keywords Found\n([\s\S]+?)(?=###|$)/);
                                let keyword_matches = [];
                                if (keywordsMatch) {
                                    const keywordsContent = keywordsMatch[1];
                                    // Extract individual keywords from the list
                                    const keywordLines = keywordsContent.split('\n').filter(line => line.trim().startsWith('- '));
                                    keyword_matches = keywordLines.map(line => {
                                        // Extract just the keyword part (remove "- " and any count info)
                                        const keyword = line.replace(/^- /, '').split('(')[0].trim();
                                        return keyword;
                                    });
                                }
                                
                                // Parse is_new status from the markdown
                                const isNewMatch = section.match(/- \*\*Is New:\*\* (.+?)\n/);
                                let is_new = true; // Default to true if not found
                                if (isNewMatch) {
                                    const isNewValue = isNewMatch[1].trim().toLowerCase();
                                    is_new = (isNewValue === 'true');
                                }
                                
                                laws.push({
                                    title: titleMatch[1].trim(),
                                    published: publishedMatch ? publishedMatch[1].trim() : 'Unknown',
                                    link: linkMatch ? linkMatch[1].trim() : '',
                                    relevance_score: scoreMatch ? parseFloat(scoreMatch[1]) : 0,
                                    ai_description: summaryMatch ? summaryMatch[1].trim() : 'No summary available',
                                    is_new: is_new,
                                    source: websiteKey,
                                    keyword_matches: keyword_matches
                                });
                            }
                        }
                    }
                    
                    return laws;
                });
                
                console.log('Loaded laws from markdown:', lawsData);
                console.log('Available websites from API:', availableWebsites);
                
                // Log all unique sources found
                const uniqueSources = [...new Set(lawsData.map(law => law.source))];
                console.log('Unique law sources:', uniqueSources);
                
                // Sort laws by relevance score (descending) before displaying
                lawsData.sort((a, b) => b.relevance_score - a.relevance_score);
                displayLaws(lawsData);
            }
        } catch (error) {
            console.error('Failed to load markdown files:', error);
            lawsData = [];
            displayLaws(lawsData);
        }
    }

    // Display laws in the UI
    function displayLaws(laws) {
        lawsContainer.innerHTML = '';
        
        if (laws.length === 0) {
            lawsContainer.innerHTML = '<p>No laws found matching your criteria.</p>';
            return;
        }

        laws.forEach(law => {
            const lawCard = document.createElement('div');
            lawCard.className = 'law-card';
            
            lawCard.innerHTML = `
                <h2>${law.title} ${law.is_new ? '<span class="new-badge">NEW</span>' : ''}</h2>
                <div class="law-meta">
                    <span>Published: ${law.published}</span>
                    <span class="relevance-score">Relevance: ${law.relevance_score}</span>
                </div>
                <div class="ai-summary">
                    <h3>AI Summary</h3>
                    <p>${law.ai_description}</p>
                </div>
                <div class="keywords">
                    ${law.keyword_matches?.map(keyword => `<span>${keyword}</span>`).join('') || ''}
                </div>
                <a href="${law.link}" class="law-link" target="_blank">View full text →</a>
            `;
            
            lawsContainer.appendChild(lawCard);
        });
    }

    // Search functionality
    function handleSearch() {
        const searchTerm = searchInput.value.toLowerCase();
        let filteredLaws = lawsData;

        console.log('🔍 Starting search/filter operation');
        console.log('Total laws:', lawsData.length);
        console.log('Current website filter:', currentWebsiteFilter);
        console.log('Current date filter:', currentDateFilter);

        // Note: Category filtering is now handled server-side when fetching laws
        // All laws in lawsData already belong to the selected category (if any)
        console.log('Current category filter:', currentWebsiteFilter);

        // Apply date range filter
        if (currentDateFilter && currentDateFilter !== 'all') {
            const now = new Date();
            now.setHours(23, 59, 59, 999); // Set to end of day
            const threshold = new Date(now);

            // Set threshold based on filter type
            if (currentDateFilter === 'week') {
                threshold.setDate(now.getDate() - 7);
                threshold.setHours(0, 0, 0, 0); // Set to start of day
            } else if (currentDateFilter === 'month') {
                threshold.setDate(now.getDate() - 30);
                threshold.setHours(0, 0, 0, 0); // Set to start of day
            }

            console.log('Current date:', now.toISOString());
            console.log('Date threshold:', threshold.toISOString());

            filteredLaws = filteredLaws.filter(law => {
                const publishedDate = parsePublishedDate(law.published);
                if (!publishedDate) {
                    console.log(`Could not parse date for law: ${law.title}, date: ${law.published}`);
                    return false;
                }

                if (currentDateFilter === 'date_desc' || currentDateFilter === 'date_asc') {
                    return true; // Don't filter by date range for sorting options
                }
                
                // For week/month filters, check if date is within range
                const isWithinRange = publishedDate >= threshold && publishedDate <= now;
                console.log(`Law: ${law.title}`);
                console.log(`Published: ${publishedDate.toISOString()}`);
                console.log(`Is between ${threshold.toISOString()} and ${now.toISOString()}: ${isWithinRange}`);
                return isWithinRange;
            });
        }

        console.log('After date filter:', filteredLaws.length);

        // Apply search term if provided
        if (searchTerm) {
            filteredLaws = filteredLaws.filter(law => {
                const titleMatch = law.title.toLowerCase().includes(searchTerm);
                const descriptionMatch = law.ai_description && law.ai_description.toLowerCase().includes(searchTerm);
                const keywordMatch = law.keyword_matches && law.keyword_matches.some(keyword => 
                    keyword.toLowerCase().includes(searchTerm)
                );
                
                const matches = titleMatch || descriptionMatch || keywordMatch;
                
                if (matches) {
                    console.log(`Search match found in: ${law.title}`);
                }
                return matches;
            });
        }

        console.log('Final filtered laws:', filteredLaws.length);
        
        // Apply sorting based on the selected option
        if (currentDateFilter === 'date_desc') {
            // Sort by date descending (newest first)
            filteredLaws.sort((a, b) => {
                const dateA = parsePublishedDate(a.published);
                const dateB = parsePublishedDate(b.published);
                
                // Handle invalid dates by putting them at the end
                if (!dateA && !dateB) return 0;
                if (!dateA) return 1;
                if (!dateB) return -1;
                
                return dateB - dateA;
            });
        } else if (currentDateFilter === 'date_asc') {
            // Sort by date ascending (oldest first)
            filteredLaws.sort((a, b) => {
                const dateA = parsePublishedDate(a.published);
                const dateB = parsePublishedDate(b.published);
                
                // Handle invalid dates by putting them at the end
                if (!dateA && !dateB) return 0;
                if (!dateA) return 1;
                if (!dateB) return -1;
                
                return dateA - dateB;
            });
        } else {
            // Default: sort by relevance score (descending)
            filteredLaws.sort((a, b) => b.relevance_score - a.relevance_score);
        }
        
        // Update stats
        if (typeof updateStats === 'function') {
            updateStats(filteredLaws.length);
        }
        
        displayLaws(filteredLaws);
    }
    
    function parsePublishedDate(dateStr) {
        if (!dateStr || dateStr === 'Unknown') return null;

        console.log('Parsing date:', dateStr);

        // Try parsing ISO format with timezone
        if (dateStr.includes('T')) {
            const d = new Date(dateStr);
            if (!isNaN(d.getTime())) {
                console.log('Parsed as ISO format:', d.toISOString());
                return d;
            }
        }

        // Try parsing RFC 2822 format (e.g. Thu, 14 Aug 2025 00:00:00 +0800)
        if (dateStr.includes(',')) {
            try {
                const parsed = Date.parse(dateStr);
                if (!isNaN(parsed)) {
                    const d = new Date(parsed);
                    console.log('Parsed as RFC 2822:', d.toISOString());
                    return d;
                }
            } catch (e) {
                console.log('Failed to parse RFC 2822 date:', dateStr);
            }
        }

        // Try extracting YYYY-MM-DD from various formats
        const dateRegex = /(\d{4})[-/](\d{1,2})[-/](\d{1,2})/;
        const match = dateStr.match(dateRegex);
        if (match) {
            const [_, year, month, day] = match;
            const d = new Date(year, parseInt(month) - 1, parseInt(day));
            if (!isNaN(d.getTime())) {
                console.log('Parsed as YYYY-MM-DD:', d.toISOString());
                return d;
            }
        }

        // Try extracting date from text format (e.g., "14 August 2025")
        const textMatch = dateStr.match(/(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})/i);
        if (textMatch) {
            const monthMap = {
                jan: 0, feb: 1, mar: 2, apr: 3, may: 4, jun: 5,
                jul: 6, aug: 7, sep: 8, oct: 9, nov: 10, dec: 11
            };
            const [_, day, monthStr, year] = textMatch;
            const month = monthMap[monthStr.toLowerCase().substring(0,3)];
            const d = new Date(parseInt(year), month, parseInt(day));
            if (!isNaN(d.getTime())) {
                console.log('Parsed as text format:', d.toISOString());
                return d;
            }
        }

        console.log('Failed to parse date:', dateStr);
        return null;
    }

    // Keyword editing functionality
    async function loadKeywords() {
        await loadInitialKeywords();
        keywordsTextarea.value = DSO_KEYWORDS.join('\n');
    }

    async function saveKeywords() {
        try {
            const keywords = keywordsTextarea.value
                .split('\n')
                .map(k => k.trim())
                .filter(k => k.length > 0);
            
            // Update local keywords array
            DSO_KEYWORDS = keywords;

            loadingDiv.textContent = 'Filtering or scraping laws...';
            
            // Save to keywords.json
            const response = await fetch('/save_keywords', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ keywords })
            });

            if (!response.ok) {
                throw new Error('Failed to save keywords');
            }

            const filteredLaws = await response.json();

            alert('Keywords updated successfully!');
            keywordModal.style.display = 'none';
            lawsData = filteredLaws;
            displayLaws(filteredLaws);
            loadingDiv.textContent = '';
            //fetchLaws(currentDateFilter); // Refresh laws with new keywords
        } catch (e) {
            alert(`Error updating keywords: ${e.message}`);
        }
    }

    // Load initial keywords from keywords.json
    let DSO_KEYWORDS = [];
    async function loadInitialKeywords() {
        try {
            const response = await fetch('/keywords.json');
            if (response.ok) {
                const json = await response.json();
                DSO_KEYWORDS = json.keywords || [];
                return true;
            }
            return false;
        } catch (e) {
            console.error('Failed to load keywords:', e);
            return false;
        }
    }
    loadInitialKeywords().catch(e => console.error('Initial keyword load failed:', e));

    // Function to scrape all websites using the new API endpoint
    async function scrapeAllWebsites() {
        try {
            loadingDiv.textContent = 'Scraping all websites...';
            
            const response = await fetch('/api/scrape-all', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const result = await response.json();
            
            if (result.success) {
                // Show summary of scraping results
                const successCount = Object.values(result.results_by_website).filter(r => typeof r === 'number').length;
                const totalRelevant = result.total_results;
                
                alert(`Scraping completed!\n\nSuccessfully scraped ${successCount} websites\nFound ${totalRelevant} relevant items total`);
                
                // Refresh the laws display with all data
                await loadMarkdownFiles();
            } else {
                alert(`Scraping failed: ${result.error}`);
            }
            
            loadingDiv.textContent = '';
        } catch (error) {
            loadingDiv.textContent = 'Error scraping websites';
            console.error('Scrape all error:', error);
            alert(`Scraping failed: ${error.message}`);
        }
    }

    // Event listeners
    searchInput.addEventListener('input', handleSearch);
    websiteSelect.addEventListener('change', (e) => {
        currentWebsiteFilter = e.target.value;
        if (currentWebsiteFilter === 'all') {
            // Load all laws if "All Categories" is selected
            fetchLaws(currentDateFilter);
        } else {
            // Fetch laws by specific category
            fetchLawsByCategory(currentWebsiteFilter);
        }
    });
    refreshBtn.addEventListener('click', () => {
        if (currentWebsiteFilter === 'all') {
            fetchLaws(currentDateFilter);
        } else {
            fetchLaws(currentDateFilter, currentWebsiteFilter);
        }
    });
    // Add scrape all button functionality
    document.getElementById('scrapeAll').addEventListener('click', scrapeAllWebsites);
    dateFilter.addEventListener('change', (e) => {
        currentDateFilter = e.target.value;
        // Apply client-side filtering instead of re-fetching
        handleSearch();
    });
    editKeywordsBtn.addEventListener('click', () => {
        loadKeywords();
        keywordModal.style.display = 'block';
        setTimeout(() => {
            keywordModal.classList.add('show');
        }, 10);
    });
    saveKeywordsBtn.addEventListener('click', saveKeywords);
    cancelEditBtn.addEventListener('click', () => {
        keywordModal.classList.remove('show');
        setTimeout(() => {
            keywordModal.style.display = 'none';
        }, 300);
    });
    window.addEventListener('click', (e) => {
        if (e.target === keywordModal) {
            keywordModal.classList.remove('show');
            setTimeout(() => {
                keywordModal.style.display = 'none';
            }, 300);
        }
    });

    // Initial load
    fetchWebsites();
    fetchLaws(currentDateFilter);
});
