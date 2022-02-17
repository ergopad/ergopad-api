scalaVersion := "2.12.12"
scalacOptions += "-language:higherKinds"
addCompilerPlugin("org.typelevel" %% "kind-projector" % "0.10.3" cross CrossVersion.binary)

scalacOptions += "-Ydelambdafy:inline"
lazy val sonatypePublic = "Sonatype Public" at "https://oss.sonatype.org/content/groups/public/"
lazy val sonatypeReleases = "Sonatype Releases" at "https://oss.sonatype.org/content/repositories/releases/"
lazy val sonatypeSnapshots = "Sonatype Snapshots" at "https://oss.sonatype.org/content/repositories/snapshots/"

resolvers ++= Seq(Resolver.mavenLocal, sonatypeReleases, sonatypeSnapshots, Resolver.mavenCentral)

scalacOptions ++= Seq(
  "-deprecation",
  "-encoding", "UTF-8",
  "-feature",
  "-unchecked"
)

libraryDependencies ++= Seq(
  "org.ergoplatform" % "ergo-scala-compiler_2.12" % "0.0.0-32-aaadbee1-SNAPSHOT",
  "org.ergoplatform" % "ergo-appkit_2.12" % "develop-d77acfb8-SNAPSHOT"
)
libraryDependencies += "org.slf4j" % "slf4j-nop" % "1.7.21"