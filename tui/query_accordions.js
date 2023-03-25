(query) => {
    const accordions = document.getElementById("accordion__body-HOTEL").children[0].children[0].children;

    for (const a of accordions) {
        const [ name, benefits ] = a.children;
        if (name.textContent === query) {
            return Array.from(benefits.children).map((element) => element.textContent);
        }
    }

    return [];
}

