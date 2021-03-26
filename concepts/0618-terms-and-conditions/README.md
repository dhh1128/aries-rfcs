# 0618: Composable Terms and Conditions (CTCs)
- Authors: [Daniel Hardman](daniel.hardman@gmail.com)
- Status: [PROPOSED](/README.md#proposed)
- Since: 2021-03-19
- Status Note: Builds on a conversation in an Aries Community B call on 2021-03-17, as well as on ideas from customercommons.org and a Googld Doc circulated in 2017.
- Start Date: 2021-03-19
- Tags: [concept](/tags.md#concept)

## Summary

Explains how DIDComm-based interactions can be conditioned on the acceptance of terms and conditions in a way that is both machine-readable and human-friendly.

## Motivation

Many interactions should only take place if both parties have a shared agreement of the constraints and assumptions that apply. Conveying these semantics has traditionally involved long documents full of legal concepts -- with new documents each time the interaction partner changes. Acceptance is a take-it-or-leave it proposition, and typically binds one party far more than the other. UX designers are left with a lose-lose proposition -- either bury the user in details, or hide the details and blame the user if they don't read them. 

![eulas](eulas.png)

The result is that [current mechanisms provide value mostly to the institutions whose lawyers crafted them](https://www.theatlantic.com/technology/archive/2012/04/behold-a-terms-of-service-agreement-that-is-actually-user-friendly/255803/). (Search for "EULA memes" on the web to share some rueful chuckles about this truth...)

We need a better way, and we need it to be a first-class feature of the DIDComm ecosystem.

## Tutorial

Terms and conditions are a complex topic. During the design of the [W3C Verifiable Credentials data model standard](https://www.w3.org/TR/vc-data-model/), serious efforts were made to include support for such a feature. Unfortunately, the breadth of requirements and perspectives made progress untenable, and the feature was deferred. See [Prior Art](#prior-art) for a discussion of other thinking on the topic.

We intend for the Composable Terms and Conditions (CTC) mechanism presented here to be flexible and powerful -- but also easy to understand and implement, in its most common form. This should address the needs of a very diverse audience. However, such an ambitious goal means that the RFC is long, and it requires an investment to understand its subtleties. We have to cover some deep background information, so the eventual simplifications and the possible advanced usages will all make sense.

### Relationship to Other Mechanisms

[DIDComm protocols](../0003-protocols/README.md) answer the question: _"**How** will we structure this interaction?"_

[Goal codes](../0519-goal-codes/README.md) answer the question: _"**Why** are we interacting?"_

Composable Terms and Conditions (CTCs) answer the question: _"**Under what conditions** are we interacting?"_ This is a somewhat narrow question within the larger scope of concerns for [machine-readable governance frameworks](../0430-machine-readable-governance-frameworks/README.md). CTCs are intended to be used by some governance framework features; they can also be used independently.

To understand the role of CTCs, consider these two scenarios:

1. Acme (an airline) asks Bob (a passenger) to prove he's been vaccinated against the COVID-19 virus.
2. Carol sends a "let's play chess" message to Deepak.

In scenario 1, _How?_ is clearly a protocol like [Present Proof 2.0](../../featrues/../features/0454-present-proof-v2/README.md). _Why?_ could be a goal code about boarding a plane, or about maintaining a loyalty program status, or about entering a frequent flyer lounge. _Under what conditions_ (the role of CTCs) might be: "I will reveal my vaccination status if you promise not to disclose it to a third party; I agree to notify you immediately if I notice symptoms of an infection."

In scenario 2, _How?_ is a chess protocol. _Why?_ could be for fun, instruction, or formal competition. _Under what conditions_ (the role of CTCs) might specify how results will be published and what [rule variant](https://en.wikipedia.org/wiki/List_of_chess_variants) applies.

### Legal Rigor vs. User Friendliness vs. Machine Readability

One of the challenges with terms and conditions is that lawyers write them to protect their employers in court -- but ordinary people have to read and agree to them. Satisfying both audiences [can be hard](https://blog.clausehound.com/how-do-i-make-a-terms-and-conditions-user-friendly-while-also-protecting-my-legal-rights/). And DIDComm introduces an additional audience -- an agent that will automate behaviors according to policy. This compounds the difficulty.

The approach that we take here addresses this tension in several ways:

1. Contractual content is modeled as a [Ricardian contract](https://en.wikipedia.org/wiki/Ricardian_contract), guaranteeing that legal, human language is also always machine-parseable.
2. We establish and recommend a [friendliness convention](#friendliness-convention) that allows formal, legal language to be associated with simple summaries.
3. We apply a [naming technique](#named-reusable-clauses) similar to the one used used to build and name Creative Commons licenses. This lets common provisions become familiar to users, and allows them to be combined and reused from a [Condition Registry](#condition-registry) in intuitive ways.

### How to Propose and Accept

Composable terms and conditions (CTCs) have to be proposed and accepted.

The simplest way to do this is to emulate the familiar process of accepting a EULA. An institution proposes CTCs in the first message of a protocol, and signals that continuation of the protocol depends on acceptance. An individual then signals their acceptance in the next message they send, and the protocol in question proceeds as designed. No new protocol is needed, and no new steps are added to the protocol in question -- whether it's credential issuance, presenting proof, payment, applying for a loan, making a connection, applying for a loan, etc.

However, the conceptual model for CTCs allows other choices. Institutions and individuals are peers in the CTC mechanism, so individuals can have CTCs, and use them to bind an institution (or another individual) just as easily. Semantics for each party are mapped to named roles, rather than implicitly deriving from which party proposes the terms -- so either a buyer or a seller can propose terms, at any point in an interaction, and in any order, with the same effect. More than two parties can be involved. CTCs can also be negotiated until all parties are in alignment.

We will provide concrete examples of how to model all of these possibilities. Let's begin by exploring the data that's needed to fully describe a condition.

### Condition Binding

A __condition binding__ associates an __abstract condition__ with one or more __condition arguments__ that make it concrete.

An abstract condition is a piece of text that expresses a condition in human language, using curly braces to delimit __condition parameters__ that must be bound to arguments. For example:

```handlebars
{{Seller}} agrees not to resell {{Buyer}} PII.
```

Here, `{{Buyer}}` and `{{Seller}}` are parameters to the condition, and must be bound to make the condition concrete.

A binding is expressed in a JSON structure like this:

```jsonc
{
    // "ac" = abstract condition
    "ac": "{{Seller}} agrees not to resell {{Buyer}} PII.",
    // "args" provide values for each parameter
    "args": {
        "Seller": "did:example:1", // Alice's DID
        "Buyer": "did:example:2" // Bob's DID
    }
}
```

For the sake of our introductory narrative here, we are showing inlined text content for `ac`; more commonly we would attach and link it using `acref` instead. But the principle is the same in either case; our condition binding requires us to specify the abstract condition plus its args. (See [Referencing Conditions by URI](#referencing-conditions-by-uri) below, as well as &gt; Condition Binding](#condition-binding) and [Reference &gt; Abstract Conditions](#abstract-condition) for more details.)

### Multiple Conditions

It's common to compose legal contracts from one or more clauses. In some cases, general provisions of a contract are also superseded or overruled by more specific clauses in narrower circumstances. These semantics are modeled by building an *array of CTCs*. Ordering in a CTC array expresses precedence, with later items supplementing, narrowing, and overriding earlier items.

In [DIDComm v1](../0005-didcomm/README.md#v1-vs-v2), a condition binding array is attached to a message with a `~ctcs` decorator. In [DIDComm v2](https://identity.foundation/didcomm-messaging/spec/), this becomes a `ctcs` header. The array structure is the same in either case.

### Referencing Conditions by URI

It is inefficient to embed the full text of potentially lengthy terms and conditions in what would otherwise be terse DIDComm messages. Therefore, the content of an abstract condition should typically be included by reference rather than by value, using DIDComm's attachment mechanism ([appended + hashed + linked](https://github.com/hyperledger/aries-rfcs/blob/master/concepts/0017-attachments/README.md#appending)). This indirection helps software recognize repeated and cacheable CTCs, allows signing, and provides scaffolding upon which [named, reusable clauses](#named-reusable-clauses) can build a much simplified UX.

A canonical reference to abstract condition content therefore replaces the `ac` field with an `acref` in a pattern that looks like this:

```jsonc
{
    // ... other parts of the message ...
    "~ctcs": [
        {   // This is a reference to the id of an attached abstract
            // condition.
            "acref": "#attach1", 
            "args": {"buyer": "did:example1", "seller": "did:example2"}
        }
    ],
    // ... other parts of the message ...
    "~attach": [
        {
            // This is the id that was referenced in ~ctcs.acref, above.
            "id": "attach1",
            "media-type": "text/markdown",
            "data": {
                // Instead of including the content of the Ricardian contract,
                // we provide its hash and a place where it can be downloaded
                // This facilitates caching and keeps message sizes small.
                "hash": "0a803d699d8cc3b827ef74c0270a3638f2f8708a0af6590f2114a08561c891de",
                "url": "https://customercommons.org/ctcs/hold-buyer-harmless"
            }
        }
    ]
}
```

### Named Reusable Clauses

When abstract conditions are written for general use, and when they are referenced by a consistent URI, it becomes possible to use a short, meaningful, user-friendly name to refer to them. Instead of a URI like `https://github.com/hyperledger/aries-rfcs/blob/main/concepts/0618-terms-and-conditions/#single-use`, a name like `@single-use` can be used.

This strategy is used effectively by [Creative Commons](https://creativecommons.org/), which defines a number of standard building blocks that can be used to compose a license on intellectual property. The most common combinations of terms are named and even have common icons and abbreviations: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). The [Customer Commons initiative](customercommons.org) has begun to develop a similar idea with regard to customers licensing the data that companies learn about them.

Likewise, instead of using `ac` to incorporate the text of an abstract condition directly, or `acref` to incorporate the text by hyperlinked attachment, the `acnames` field can be used to reference one or more abstract conditions that appears in the registry below. This yields a greatly simplified CTC:

```jsonc
{
    // ... other parts of the message ...
    "~ctcs": [
        {"acnames": "@single-use @share-alike #restricted-time(3w)", "args": {"buyer": "did:example1", "seller": "did:example2"}}
    ],
}
```

---

### Scope

Normally, the scope of a CTC is the protocol in question, as well as any coprotocols that the current protocol triggers while it executes. However, other scopes are possible:

* All "runs" of the same protocol.
* All "runs" of a protocol with the same goal code.
* The connection itself.
* A particular time-frame.

### Default Roles as Parameters
Many abstract conditions establish a legal relationship between two roles. In credential contexts, it is natural to call these roles `{{Holder}}` and `{{Verifier}}` (or `{{Prover}}` and `{{Verifier}}`, or `{{Issuer}}` and `{{Holder}}`); in financial contexts, `{{Buyer}}` and `{{Seller}}` might make sense; in educational contexts, `{{Teacher}}` and `{{Student}}`.


## Reference

### Abstract Conditions

An abstract condition is a [Ricardian contract](https://en.wikipedia.org/wiki/Ricardian_contract) formatted as [CommonMark-style markdown](https://commonmark.org/), using [Handlebars templating](https://handlebarsjs.com/). Essentially, this matches the format adopted by [eos.io's Ricardian Contract Specification](https://github.com/EOSIO/ricardian-spec), except that we expect the DIDComm version to use only a small subset of those features. Specifically:

* No YAML metadata is supported.
* Handlebars is only used for simple variable substitution, not structural transformation (no `{{each}}` or `{{with}}`, etc.).
  
The net effect is that, if desired, the contract can be rendered in human-friendly form with a very simple markdown transformer, and variable substitution can be performed by simple regex search-and-replace.

### Friendliness Convention

We recommend the technique that was used to build [user-friendly terms of service on 500px.com](https://500px.com/terms): juxtapose legal language and its friendly summary. To do this in a Ricardian contract that will render via markdown, use the following convention:

Just prior to any header that you intend to summarize, create an HTML5 `<aside class="friendly">...</aside>` tag that gives a brief overview of the section that follows, as in:

```markdown
<aside class="friendly">Basically, if you don't agree with our data, open a support ticket and we'll try to fix it.</aside>

## Right to Dispute
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Quisque eleifend non ex eu luctus. Nullam ornare et leo eget auctor. Nam magna lacus, semper ut leo a, fermentum sollicitudin risus. Suspendisse potenti. Integer ullamcorper iaculis ante et efficitur. Vestibulum pharetra sem ac ipsum faucibus, eget suscipit arcu lacinia.
```

Note the need for a blank line between the header and the aside.

This technique works with all CommonMark renderers, including Github and HackMD. It allows CSS styling. In browsers that don't support HTML5 (exceedingly rare nowadays), the `<aside>` just renders like a `<p>`.

### Registry

#### @single-use
This condition applies to data e data is shared only for the purpose of completing the interaction at hand. The recipient agrees to delete it as soon as this interaction completes. Example: An eBay-style purchase might require that the seller receive the buyer’s shipping address. A shipping address shared with the Single-Use proviso during checkout should be deleted as soon as the shipment is underway. 

#### @sufferance
The data is shared for repeated use by the recipient, with no end date or end conditions. However, the data subject may alter the terms of use in the future, and if the alteration in terms is unacceptable to the data controller, the data controller acknowledges that it will thereby incur a duty to delete. In other words, the controller uses the data at the ongoing sufferance of its owner.

## Drawbacks

Why should we *not* do this?

## Rationale and alternatives

- Why is this design the best in the space of possible designs?
- What other designs have been considered and what is the rationale for not
choosing them?
- What is the impact of not doing this?

## Prior art

-  The [Kantara Initiative spec for consent receipts](https://kantarainitiative.org/download/7902/) overlaps the problem domain of this RFC in interesting but limited ways. It includes an excellent discussion about how to describe terms and conditions, and it contemplates references to privacy policies that resemble the mechanism described here.
  
    However, aligning with [ISO 29100](https://www.iso.org/standard/45123.html), the Kantara work defines consent as a principal's "freely given, specific and informed agreement to the processing of their PII." This frames consent entirely as a data processing issue, where the data in question is PII; it does not cover more generalized consent (e.g., consent to be attributed by a reporter "on the record", to receive medical treatment, to arbitration in the event of a dispute). It also does not consider agreement to general contract provisions &mdash; only to the subset of a contract that involves data processing. And it is one-way: the data processor undertakes some services and seeks consent from the data subject. The data processor never consents to proposals by the data subject.

- [Aries RFC 0167](https://github.com/hyperledger/aries-rfcs/blob/master/concepts/0167-data-consent-lifecycle/README.md) describes a method to issue and verify Kantara data processing consent receipts in the agent-oriented ecosystem of Aries. It therefore builds on the goodness of the Kantara efforts, but shares in the same narrowness of application.
  
- Websites such as termly.io, rocketlawyer.com, clausehound.com, privacypolicygenerator.info, and eulatemplate.com are in the business of helping companies generate complete contracts (often, terms of use) from standard boilerplate. They typically feature an interview process that allows clients to specify a few variables. In this respect, they are quite similar to the concept of abstract conditions and args that make those conditions concrete. However, they don't work in a standardized way, and they provide no way to link their output to DIDComm messages.

## Unresolved questions

- What parts of the design do you expect to resolve through the
enhancement proposal process before this gets merged?
- What parts of the design do you expect to resolve through the
implementation of this feature before stabilization?
- What related issues do you consider out of scope for this 
proposal that could be addressed in the future independently of the
solution that comes out of this doc?
   
## Implementations

The following lists the implementations (if any) of this RFC. Please do a pull request to add your implementation. If the implementation is open source, include a link to the repo or to the implementation within the repo. Please be consistent in the "Name" field so that a mechanical processing of the RFCs can generate a list of all RFCs supported by an Aries implementation.

*Implementation Notes* [may need to include a link to test results](/README.md#accepted).

Name / Link | Implementation Notes
--- | ---
 | 

