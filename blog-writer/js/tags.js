// Tag suggestions (ported from blog/scripts/auto_tag.py)

const TAG_KEYWORDS = {
  'linear algebra': [1, ['linear algebra', 'matrices', 'vector space', 'row reduction']],
  'eigenvalue': [1, ['eigenvalue', 'eigenvector', 'eigenspace']],
  'statistics': [1, ['statistics', 'statistical', 'hypothesis test', 'p-value', 'confidence interval']],
  'probability': [1, ['probability', 'probabilistic', 'expected value', 'random variable']],
  'combinatorics': [1, ['combinatorics', 'combinatorial', 'binomial coefficient']],
  'geometry': [1, ['geometry', 'geometric', 'polygon', 'fractal', 'tesselation']],
  'number theory': [1, ['number theory', 'prime number', 'modular arithmetic']],
  'dynamical systems': [1, ['dynamical system', 'differential equation', 'attractor']],
  'calculus': [1, ['calculus', 'derivative', 'integral', 'taylor series']],
  'graph': [1, ['graph theory', 'adjacency matrix', 'vertex', 'vertices']],
  'math': [2, ['mathematic', 'theorem', 'proof', 'lemma', 'conjecture', 'equation']],
  'music': [1, ['music', 'album', 'musician', 'composer', 'melody', 'symphony']],
  'concert': [1, ['concert', 'live performance', 'recital']],
  'piano': [1, ['piano', 'pianist']],
  'cello': [1, ['cello', 'cellist']],
  'classical': [1, ['classical music', 'baroque', 'vivaldi', 'beethoven', 'mozart']],
  'linux': [1, ['linux', 'ubuntu', 'gnome', 'sudo apt']],
  'bash': [1, ['#!/bin/bash', 'bash script', 'bash command']],
  'python': [1, ['python3', 'import numpy', 'import pandas', '.py ', 'pip install']],
  'sage': [1, ['sagemath', 'sage(']],
  'teaching': [2, ['teaching', 'classroom', 'students', 'instructor', 'syllabus', 'lecture', 'course']],
  'education': [1, ['education', 'curriculum', 'pedagogy']],
  'life': [2, ['my life', "i've been", 'personal', 'recently']],
  'philosophy': [1, ['philosophy', 'philosophical', 'epistemolog']],
  'observation': [1, ['observation', 'i noticed', 'interesting pattern']],
  'depression': [1, ['depression', 'depressed', 'mental health']],
  'movie': [1, ['movie', 'film', 'cinema', 'director']],
  'book': [1, ['book review', 'i read a book', 'this book']],
  'poetry': [1, ['poem', 'poetry', 'stanza']],
  'politics': [1, ['politics', 'political', 'government', 'democracy']],
  'immigration': [1, ['immigration', 'immigrant', 'visa', 'citizenship', 'refugee']],
  'racism': [1, ['racism', 'racist', 'racial discrimination']],
  'publication': [2, ['published', 'journal', 'accepted', 'peer review']],
  'paper': [1, ['our paper', 'this paper', 'the paper', 'manuscript']],
  'talk': [1, ['gave a talk', 'seminar talk', 'my talk', 'invited talk']],
  'conference': [1, ['conference', 'workshop', 'symposium']],
  'academia': [2, ['academia', 'academic', 'university', 'professor', 'faculty', 'department']],
  'finance': [1, ['finance', 'financial', 'tax', 'budget', 'investment']],
  'health': [1, ['bpa', 'bisphenol', 'endocrine disruptor']],
  'privacy': [1, ['privacy', 'end-to-end encryption', 'e2ee', 'surveillance']],
};

const BROAD_TAGS = new Set([
  'math', 'music', 'linux', 'teaching', 'life', 'politics', 'publication', 'finance',
]);

export function suggestTags(content, existingTags = []) {
  const lower = content.toLowerCase();
  const existingSet = new Set(existingTags.map(t => t.trim().toLowerCase()));

  const scores = {};
  for (const [tag, [minHits, keywords]] of Object.entries(TAG_KEYWORDS)) {
    if (existingSet.has(tag)) continue;
    const hits = keywords.filter(kw => lower.includes(kw.toLowerCase())).length;
    if (hits >= minHits) {
      scores[tag] = hits;
    }
  }

  let suggested = Object.keys(scores).sort((a, b) => scores[b] - scores[a]);
  if (suggested.length > 6) suggested = suggested.slice(0, 6);

  // Ensure at least one broad category
  const hasBroad = [...existingSet, ...suggested].some(t => BROAD_TAGS.has(t));
  if (!hasBroad) suggested.push('life');

  return suggested;
}
