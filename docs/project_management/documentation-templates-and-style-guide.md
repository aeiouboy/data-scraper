# Documentation Templates and Style Guide
## RIS Data Scrap Project

**Version:** 1.0  
**Date:** 2025-07-21  
**Purpose:** Ensure consistent, professional documentation across the project

---

## Overview

This guide provides templates and standards for all project documentation. Following these guidelines ensures consistency, maintainability, and professional appearance across all Markdown files in the RIS Data Scrap project.

---

## Style Guide

### Writing Style

#### **Tone and Voice**
- **Professional but approachable**: Technical content that's accessible
- **Active voice preferred**: "Configure the API" vs "The API should be configured"
- **Clear and concise**: Avoid unnecessary jargon or complexity
- **User-focused**: Write from the reader's perspective

#### **Language Standards**
- **American English spelling**: "organization" not "organisation"
- **Technical terms**: Define acronyms on first use
- **Consistent terminology**: Use the same terms throughout (e.g., "endpoint" not "API route")

#### **Content Principles**
1. **Start with the goal**: What will the reader accomplish?
2. **Provide context**: Why is this important?
3. **Give clear steps**: How to achieve the goal
4. **Include examples**: Show, don't just tell
5. **Link to related content**: Help readers find more information

### Formatting Standards

#### **Headers**
```markdown
# Main Title (H1) - Only one per document
## Major Section (H2)
### Subsection (H3)
#### Detail Section (H4)
```

#### **Code Blocks**
```markdown
# Inline code
Use `backticks` for inline code references.

# Code blocks with language
```bash
npm install
```

```python
def example_function():
    return "Hello, World!"
```
```

#### **Lists**
```markdown
# Unordered lists
- Use hyphens for bullet points
- Be consistent with indentation
  - Indent with two spaces
  - Keep alignment clean

# Ordered lists
1. Use numbers for sequential steps
2. Each item should be actionable
3. Consider breaking long lists into sections
```

#### **Links**
```markdown
# Internal links (relative paths)
[Setup Guide](../developer-guide/setup.md)
[API Reference](./api-reference/endpoints.md)

# External links
[FastAPI Documentation](https://fastapi.tiangolo.com/)

# Link with section
[Database Setup](../developer-guide/setup.md#database-configuration)
```

#### **Tables**
```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |
```

#### **Alerts and Callouts**
```markdown
**Note:** General information or tips

**Important:** Critical information that affects functionality

**Warning:** Information about potential problems or risks

**Prerequisites:** Required knowledge or setup before proceeding
```

---

## Document Templates

### Template 1: Standard Documentation Page

```markdown
# [Document Title]

**Last Updated:** YYYY-MM-DD  
**Audience:** [Users/Developers/Operators]  
**Prerequisites:** [List any required knowledge or setup]

---

## Overview

Brief description of what this document covers and why it's important.

## Table of Contents

- [Section 1](#section-1)
- [Section 2](#section-2)
- [Examples](#examples)
- [Related Documentation](#related-documentation)

---

## Section 1

Main content sections with clear headings and subsections.

### Subsection

Detailed information with examples where appropriate.

## Section 2

Additional content sections.

## Examples

Practical examples that demonstrate the concepts.

```bash
# Command line example
echo "Hello, World!"
```

```python
# Code example
def example():
    return "This is an example"
```

## Related Documentation

- [Related Doc 1](./related-document.md) - Brief description
- [Related Doc 2](../other-section/document.md) - Brief description

---

*Last updated: [Date] | [Link to edit this page]*
```

### Template 2: README/Index Page

```markdown
# [Section Name]

Brief description of this documentation section and its purpose.

## Contents

### Quick Links
- [Getting Started](./quick-start.md) - Start here for basics
- [FAQ](./faq.md) - Common questions and answers

### Detailed Documentation
- [Document 1](./document-1.md) - Comprehensive guide to topic 1
- [Document 2](./document-2.md) - Detailed information about topic 2
- [Document 3](./document-3.md) - Advanced topics and configuration

## Related Sections

- [Developer Guide](../developer-guide/) - For development-related topics
- [API Reference](../api-reference/) - For API documentation
- [Architecture](../architecture/) - For system design information

## Getting Help

If you can't find what you're looking for:
1. Check the [FAQ](./faq.md)
2. Search the [full documentation](../README.md)
3. [Open an issue](https://github.com/project/issues) for missing documentation

---

*Documentation maintained by: [Team/Person] | Last reviewed: [Date]*
```

### Template 3: Tutorial/Guide

```markdown
# [Tutorial Title]: [What You'll Accomplish]

**Time to Complete:** [Estimated time]  
**Difficulty:** [Beginner/Intermediate/Advanced]  
**Prerequisites:** 
- [Prerequisite 1]
- [Prerequisite 2]

---

## What You'll Learn

By the end of this tutorial, you'll be able to:
- [Learning objective 1]
- [Learning objective 2]
- [Learning objective 3]

## Before You Begin

Make sure you have:
- [Required software/access]
- [Required knowledge]
- [Required setup]

---

## Step 1: [Action Title]

Brief explanation of what this step accomplishes.

### Instructions

1. [Specific action with command if applicable]
   ```bash
   command --option value
   ```

2. [Next action]
   
3. [Verification step]

**Expected Result:** Description of what should happen.

## Step 2: [Next Action Title]

Continue with clear, sequential steps.

## Troubleshooting

**Problem:** Common issue that might occur  
**Solution:** How to resolve it

**Problem:** Another potential issue  
**Solution:** Resolution steps

## Next Steps

Now that you've completed this tutorial:
- [Suggested next tutorial or topic]
- [Related advanced topic]
- [Link to deeper documentation]

## Related Resources

- [Related Tutorial](./related-tutorial.md)
- [Reference Documentation](../reference/topic.md)
- [Advanced Guide](./advanced-guide.md)
```

### Template 4: API Documentation

```markdown
# [API Endpoint/Feature Name]

**Endpoint:** `[HTTP METHOD] /api/path`  
**Version:** [API Version]  
**Authentication:** [Required/Optional/None]

---

## Overview

Brief description of what this endpoint does and when to use it.

## Request

### URL Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `param1`  | string | Yes | Description of parameter |
| `param2`  | integer | No | Optional parameter description |

### Query Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit`   | integer | 10 | Number of results to return |
| `offset`  | integer | 0 | Number of results to skip |

### Request Body
```json
{
  "field1": "string",
  "field2": 123,
  "field3": {
    "nested_field": "value"
  }
}
```

## Response

### Success Response (200 OK)
```json
{
  "status": "success",
  "data": {
    "result": "value"
  },
  "meta": {
    "total": 100,
    "count": 10
  }
}
```

### Error Responses

**400 Bad Request**
```json
{
  "status": "error",
  "message": "Invalid request parameters",
  "errors": ["Field 'field1' is required"]
}
```

**404 Not Found**
```json
{
  "status": "error",
  "message": "Resource not found"
}
```

## Examples

### Basic Request
```bash
curl -X GET "https://api.example.com/api/endpoint?limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Request with Body
```bash
curl -X POST "https://api.example.com/api/endpoint" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "field1": "value",
    "field2": 123
  }'
```

### Python Example
```python
import requests

response = requests.get(
    "https://api.example.com/api/endpoint",
    params={"limit": 5},
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

data = response.json()
```

## Related Endpoints

- [Related Endpoint 1](./related-endpoint.md)
- [Related Endpoint 2](./another-endpoint.md)

## See Also

- [Authentication Guide](../authentication.md)
- [Rate Limits](../rate-limits.md)
- [Error Handling](../error-handling.md)
```

### Template 5: Troubleshooting Guide

```markdown
# [Component/Feature] Troubleshooting

Common problems and solutions for [component/feature name].

---

## Quick Diagnostics

Before diving into specific problems, try these general steps:

1. **Check the basics**
   - Verify configuration is correct
   - Ensure all dependencies are installed
   - Check log files for error messages

2. **Common fixes**
   - Restart the service
   - Clear cache/temporary files
   - Update to latest version

---

## Common Problems

### Problem: [Descriptive Problem Title]

**Symptoms:**
- [Observable symptom 1]
- [Observable symptom 2]

**Cause:**
Brief explanation of what causes this issue.

**Solution:**
1. [Step 1 to resolve]
   ```bash
   command-to-run
   ```
2. [Step 2 to resolve]
3. [Verification step]

**Prevention:**
How to avoid this problem in the future.

---

### Problem: [Another Problem Title]

**Symptoms:**
- [Symptoms of this problem]

**Cause:**
What causes this issue.

**Solution:**
```bash
# Quick fix command
fix-command --option
```

Detailed explanation if needed.

---

## Advanced Diagnostics

### Checking Logs

```bash
# View recent logs
tail -f /path/to/logfile

# Search for specific errors
grep "ERROR" /path/to/logfile
```

### Testing Configuration

```bash
# Validate configuration
validate-config --file config.yaml

# Test connectivity
test-connection --host example.com
```

## Getting Help

If these solutions don't resolve your issue:

1. **Check the documentation**
   - [Main Documentation](../README.md)
   - [FAQ](../user-guide/faq.md)

2. **Search existing issues**
   - [GitHub Issues](https://github.com/project/issues)

3. **Create a new issue**
   - Include error messages
   - Describe steps to reproduce
   - Include system information

## Related Documentation

- [Setup Guide](./setup.md)
- [Configuration Reference](./configuration.md)
- [Log Analysis](./log-analysis.md)
```

---

## File Naming Conventions

### Standard Naming Rules

1. **Use kebab-case**: `file-name.md` (lowercase with hyphens)
2. **Be descriptive**: Names should indicate content clearly
3. **Use consistent patterns**: Similar content types use similar naming

### Naming Patterns by Type

| Content Type | Pattern | Examples |
|--------------|---------|----------|
| **Setup/Installation** | `[component]-setup.md` | `database-setup.md`, `frontend-setup.md` |
| **User Guides** | `[feature]-guide.md` | `scraping-guide.md`, `api-guide.md` |
| **Tutorials** | `[action]-tutorial.md` | `basic-scraping-tutorial.md` |
| **Troubleshooting** | `[component]-troubleshooting.md` | `api-troubleshooting.md` |
| **Reference** | `[topic]-reference.md` | `api-reference.md`, `config-reference.md` |
| **Analysis Reports** | `[topic]-analysis.md` | `performance-analysis.md` |
| **Status Reports** | `[topic]-status.md` | `migration-status.md` |

### Directory Naming

- **Use kebab-case**: `directory-name/`
- **Group by function**: `api-reference/`, `user-guide/`
- **Avoid abbreviations**: `developer-guide/` not `dev-guide/`

---

## Content Organization

### Document Structure

1. **Title and Metadata** (Required)
   - Clear, descriptive title
   - Last updated date
   - Target audience
   - Prerequisites if applicable

2. **Overview** (Required)
   - What the document covers
   - Why it's important
   - What the reader will learn

3. **Table of Contents** (For long documents)
   - Use for documents > 5 sections
   - Link to major sections

4. **Main Content** (Required)
   - Logical flow of information
   - Clear section headings
   - Examples and code blocks

5. **Related Documentation** (Recommended)
   - Links to related topics
   - Cross-references to other sections

### Section Ordering

1. **Overview/Introduction**
2. **Prerequisites/Requirements**
3. **Main Content** (logical order)
4. **Examples/Tutorials**
5. **Troubleshooting** (if applicable)
6. **Related Resources**

---

## Maintenance Guidelines

### Regular Review Schedule

- **Monthly**: Check for broken links
- **Quarterly**: Review content accuracy
- **With releases**: Update version-specific information
- **As needed**: Update when features change

### Content Ownership

| Documentation Type | Owner | Review Frequency |
|-------------------|-------|------------------|
| **User Guides** | Product Team | Monthly |
| **Developer Guides** | Engineering Team | Quarterly |
| **API Documentation** | Backend Team | With API changes |
| **Architecture** | Technical Lead | Quarterly |

### Quality Checklist

Before publishing documentation:

- [ ] **Spelling and grammar** checked
- [ ] **Links tested** and working
- [ ] **Code examples** tested and functional
- [ ] **Screenshots** current and accurate
- [ ] **Prerequisites** clearly stated
- [ ] **Cross-references** added where appropriate
- [ ] **Metadata** complete and accurate

---

## Automation and Tools

### Recommended Tools

- **Link Checking**: markdown-link-check
- **Spell Checking**: cspell
- **Formatting**: Prettier with markdown plugin
- **Documentation Site**: GitHub Pages, GitBook, or similar

### Automation Opportunities

1. **Link validation** in CI/CD pipeline
2. **Spell checking** in pull requests
3. **Auto-generation** of API docs from code
4. **Broken link alerts** for maintenance

---

*This style guide ensures consistent, professional documentation that serves all stakeholders effectively. Regular updates maintain relevance and accuracy.*