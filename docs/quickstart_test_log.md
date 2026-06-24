# Quickstart Review Log

Purpose: capture problems found while following the `mdcspc` quickstart from a fresh user perspective.

This is not a formal bug tracker. It is a working review notebook for anything that makes the guide harder to follow.

Use this file to capture:

* unclear wording
* missing context
* instructions that assume too much knowledge
* steps that happen in the wrong order
* examples that do not match the actual files
* commands that fail
* places where a plain-English guide stops feeling plain English

---

## Test context

* Date:
* Package version:
* Test folder:
* Install method:
* Python version:
* Notes:

---

## Quick notes while testing

Add rough notes here as soon as something feels wrong.

Newest notes at the top.

---

### Note 001 — what you need first

**Where I was in the guide**

What you need first

**What felt wrong**

It isn't clear, it says you need at least 2 columns but then lasts the four it can use in the example.

**Why this is a problem for a new user**

It's just not very clear, seems like it might mean users only ever use two columns

**Possible fix**

It should explain all four columns and then say it needs a minimum of date and value but also give example of generic values they could use for other two columns

**Status**

Open

### Note 002 — Step 1 Option B

**Where I was in the guide**

Step 1 Option B — If you are using Git

**What felt wrong**
not expicit that you need to be in a folder

**Why this is a problem for a new user**

could lead to errors

**Possible fix**

clearly state that you need to open a terminal or point vscode or whatever to the folder you want to clone the repo to

**Status**

Open

### Note 003 — Step 2

**Where I was in the guide**

Step 2 — Run a simple chart

**What felt wrong**

the first line instruction assumes too much knowledge mdcspc export-csv --input your_data.csv --out output_folder

**Why this is a problem for a new user**

barrier to use

**Possible fix**

clearly breakdown the command to help users build a usable command

**Status**

Open

---

## Bigger issues to fix

Move notes here when they are clearly actual changes needed.

---

## Fixed / dealt with

Move notes here once the guide has been changed and checked again.

---

## Note template

Copy this when adding a new note.

### Note XXX — short title

**Where I was in the guide**

**What felt wrong**

**Why this is a problem for a new user**

**Possible fix**

**Status**

Open
