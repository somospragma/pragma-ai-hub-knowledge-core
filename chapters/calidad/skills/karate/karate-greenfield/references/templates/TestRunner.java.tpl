package com.testing;

import com.intuit.karate.junit5.Karate;

class TestRunner {

    @Karate.Test
    Karate all() {
        return Karate.run().relativeTo(getClass());
    }
}
